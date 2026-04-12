import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta

from domain.entities.stock import Stock
from domain.repositories.stock_repository import EarlyRejected, ProgressCallback, StockRepository
from domain.value_objects.market_regime import MarketRegime
from infrastructure.market_data.data import get_all_symbols, get_trading_history, get_intraday, get_vnindex_history
from infrastructure.persistence.stock_metrics import compute_stock_metrics
from logger import get_logger

log = get_logger(__name__)

_executor = ThreadPoolExecutor(max_workers=30)
_semaphore: asyncio.Semaphore | None = None

# 500 req/min limit; each symbol costs 2 calls (history + intraday).
# The provider-level rate limiter (450 req/min) is the real throttle.
# Semaphore just caps in-flight symbols to avoid overwhelming the thread pool.
_CONCURRENCY = 10

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
    ) -> tuple[list[Stock], list[EarlyRejected]]:
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

        async def process(item: dict) -> Stock | tuple[str, str, str]:
            nonlocal processed_count
            async with sem:
                symbol = item["symbol"]
                exchange = item["exchange"]

                log.info("Fetching data for %s (%s)", symbol, exchange)
                history_fut = loop.run_in_executor(_executor, get_trading_history, symbol, fetch_days)
                intraday_fut = loop.run_in_executor(_executor, get_intraday, symbol)
                history_rows, intraday_rows = await asyncio.gather(history_fut, intraday_fut)

                stock = compute_stock_metrics(symbol, exchange, history_rows, intraday_rows, expected_fraction)
                if stock is None:
                    log.debug("No history for %s, skipping", symbol)
                    result = (symbol, exchange, "No trading history available")
                elif stock.gtgd20 < min_gtgd:
                    log.debug("Skipping %s: gtgd20=%.2f < min_gtgd=%.2f", symbol, stock.gtgd20, min_gtgd)
                    result = (symbol, exchange, f"GTGD20 {stock.gtgd20 / 1e9:.1f}B < {min_gtgd / 1e9:.0f}B")
                else:
                    result = stock

            async with counter_lock:
                processed_count += 1
                log.info("Progress: %d/%d — %s", processed_count, total, symbol)
                if on_progress:
                    await on_progress(processed_count, total, symbol)

            return result

        raw_results = await asyncio.gather(*[process(item) for item in symbols])
        stocks = [r for r in raw_results if isinstance(r, Stock)]
        early_rejected = [r for r in raw_results if isinstance(r, tuple)]
        log.info("list_stocks done: %d stocks, %d early-rejected", len(stocks), len(early_rejected))
        return stocks, early_rejected

    async def get_market_regime(self) -> MarketRegime | None:
        loop = asyncio.get_event_loop()
        rows = await loop.run_in_executor(_executor, get_vnindex_history, 40)
        if not rows or len(rows) < 20:
            log.warning("VNINDEX history insufficient (%d rows), skipping regime gate", len(rows) if rows else 0)
            return None
        closes = [r["close"] for r in rows]
        vnindex_close = closes[-1]
        ma5 = sum(closes[-5:]) / 5
        ma20 = sum(closes[-20:]) / 20
        regime = MarketRegime.from_values(close=vnindex_close, ma5=ma5, ma20=ma20)
        log.info("Market regime: %s (close=%.2f ma5=%.2f ma20=%.2f ratio=%.4f)", regime.state, vnindex_close, ma5, ma20, regime.ratio)
        return regime
