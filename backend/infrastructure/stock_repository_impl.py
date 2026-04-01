import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta

from domain.entities.stock import Stock
from domain.repositories.stock_repository import StockRepository
from crawler.crawler import get_all_symbols, get_trading_history, get_intraday
from logger import get_logger

log = get_logger(__name__)

_executor = ThreadPoolExecutor(max_workers=20)

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
    async def list_stocks(self, exchanges: set[str] | None = None, min_gtgd: float = 0.0) -> list[Stock]:
        now = datetime.now(tz=timezone(timedelta(hours=7)))
        expected_fraction = _get_expected_fraction_at_time(now.hour, now.minute)
        loop = asyncio.get_event_loop()

        log.info("list_stocks started: exchanges=%s min_gtgd=%s fraction=%.2f", exchanges, min_gtgd, expected_fraction)

        symbols = await loop.run_in_executor(_executor, get_all_symbols)
        if exchanges:
            symbols = [s for s in symbols if s["exchange"] in exchanges]
        log.info("Processing %d symbols", len(symbols))

        async def process(item: dict) -> Stock | None:
            symbol = item["symbol"]
            exchange = item["exchange"]

            history_rows = await loop.run_in_executor(_executor, get_trading_history, symbol, 60)
            if not history_rows:
                log.debug("No history for %s, skipping", symbol)
                return None

            current_price = history_rows[-1]["close"]
            history_sessions = len(history_rows)
            last20_values = [r["close"] * 1000 * r["volume"] for r in history_rows[-20:]]
            gtgd20 = sum(last20_values) / len(last20_values)

            if gtgd20 < min_gtgd:
                log.debug("Skipping %s: gtgd20=%.2f < min_gtgd=%.2f", symbol, gtgd20, min_gtgd)
                return None

            intraday_rows = await loop.run_in_executor(_executor, get_intraday, symbol)
            today_value = sum(r["price"] * 1000 * r["volume"] for r in intraday_rows) if intraday_rows else 0.0
            avg_intraday_expected = gtgd20 * expected_fraction

            return Stock(
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

        results = await asyncio.gather(*[process(item) for item in symbols])
        result = [r for r in results if r is not None]
        log.info("list_stocks done: %d stocks returned", len(result))
        return result
