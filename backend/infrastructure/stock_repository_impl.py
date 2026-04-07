import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta

from domain.entities.stock import Stock
from domain.repositories.stock_repository import ProgressCallback, StockRepository
from infrastructure.market_data.provider import get_all_symbols, get_trading_history, get_intraday
from logger import get_logger

log = get_logger(__name__)

_executor = ThreadPoolExecutor(max_workers=20)
_semaphore: asyncio.Semaphore | None = None

# 500 req/min limit; each symbol costs 2 calls (history + intraday).
# semaphore=3 + 1s sleep → max 3 symbols/sec = 6 req/sec = 360 req/min.
# You can tune _RATE_DELAY down (e.g. 0.5) or _CONCURRENCY up (e.g. 4) if it's too slow, just keep concurrency * 2 / delay < 8 req/sec.
_CONCURRENCY = 3
_RATE_DELAY = 1  # seconds to hold the semaphore after API calls

def _get_semaphore() -> asyncio.Semaphore:
    global _semaphore
    if _semaphore is None:
        _semaphore = asyncio.Semaphore(_CONCURRENCY)
    return _semaphore

INTRADAY_TIME_SLOTS = [
    (9, 0), (9, 30), (10, 0), (10, 30), (11, 0), (11, 30),
    (13, 0), (13, 30), (14, 0), (14, 30), (15, 0)
]
INTRADAY_CUMULATIVE = [0.12, 0.22, 0.30, 0.37, 0.43, 0.48, 0.56, 0.65, 0.75, 0.86, 1.00]


def _get_expected_fraction_at_time(hour: int, minute: int) -> float:
    if (hour, minute) < (9, 0):
        return 0.0
    for i, (h, m) in enumerate(INTRADAY_TIME_SLOTS):
        if (hour, minute) <= (h, m):
            if i == 0:
                return INTRADAY_CUMULATIVE[0]
            prev_h, prev_m = INTRADAY_TIME_SLOTS[i - 1]
            elapsed = (hour * 60 + minute) - (prev_h * 60 + prev_m)
            slot_len = (h * 60 + m) - (prev_h * 60 + prev_m)
            ratio = elapsed / max(slot_len, 1)
            return INTRADAY_CUMULATIVE[i - 1] + (INTRADAY_CUMULATIVE[i] - INTRADAY_CUMULATIVE[i - 1]) * ratio
    return 1.0


class StockRepositoryImpl(StockRepository):
    async def list_stocks(
        self,
        exchanges: set[str] | None = None,
        min_gtgd: float = 0.0,
        min_history_sessions: int = 0,
        on_progress: ProgressCallback | None = None,
    ) -> list[Stock]:
        now = datetime.now(tz=timezone(timedelta(hours=7)))
        expected_fraction = _get_expected_fraction_at_time(now.hour, now.minute)
        loop = asyncio.get_event_loop()

        # Convert session count → calendar days (Vietnam ~252 trading days/year) + 15-day buffer.
        fetch_days = max(int(min_history_sessions * 365 / 252) + 15, 90)
        log.info("list_stocks started: exchanges=%s min_gtgd=%s fraction=%.2f fetch_days=%d", exchanges, min_gtgd, expected_fraction, fetch_days)

        symbols = await loop.run_in_executor(_executor, get_all_symbols)
        if exchanges:
            symbols = [s for s in symbols if s["exchange"] in exchanges]
        log.info("Processing %d symbols", len(symbols))

        sem = _get_semaphore()
        total = len(symbols)
        processed_count = 0
        counter_lock = asyncio.Lock()

        async def process(item: dict) -> Stock | None:
            nonlocal processed_count
            async with sem:
                symbol = item["symbol"]
                exchange = item["exchange"]

                log.info("Fetching data for %s (%s)", symbol, exchange)
                history_fut = loop.run_in_executor(_executor, get_trading_history, symbol, fetch_days)
                intraday_fut = loop.run_in_executor(_executor, get_intraday, symbol)
                history_rows, intraday_rows = await asyncio.gather(history_fut, intraday_fut)
                await asyncio.sleep(_RATE_DELAY)

                if not history_rows:
                    log.debug("No history for %s, skipping", symbol)
                    stock = None
                else:
                    current_price = history_rows[-1]["close"]
                    history_sessions = len(history_rows)
                    last20_values = [r["close"] * 1000 * r["volume"] for r in history_rows[-20:]]
                    gtgd20 = sum(last20_values) / len(last20_values)

                    if gtgd20 < min_gtgd:
                        log.debug("Skipping %s: gtgd20=%.2f < min_gtgd=%.2f", symbol, gtgd20, min_gtgd)
                        stock = None
                    else:
                        today_value = sum(r["price"] * 1000 * r["volume"] for r in intraday_rows) if intraday_rows else 0.0
                        avg_intraday_expected = gtgd20 * expected_fraction
                        stock = Stock(
                            symbol=symbol,
                            exchange=exchange,
                            status="normal",
                            price=current_price,
                            gtgd20=gtgd20,
                            history_sessions=history_sessions,
                            today_value=today_value,
                            avg_intraday_expected=avg_intraday_expected,
                            intraday_ratio=today_value / avg_intraday_expected if avg_intraday_expected > 0 else None,
                        )

            async with counter_lock:
                processed_count += 1
                log.info("Progress: %d/%d — %s", processed_count, total, symbol)
                if on_progress:
                    await on_progress(processed_count, total, symbol)

            return stock

        results = await asyncio.gather(*[process(item) for item in symbols])
        result = [r for r in results if r is not None]
        log.info("list_stocks done: %d stocks returned", len(result))
        return result
