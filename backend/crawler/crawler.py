import os
import time
import threading
from collections import deque
from datetime import datetime, timedelta, date
from vnstock import Vnstock, change_api_key
from logger import get_logger

log = get_logger(__name__)

_api_key = os.environ.get("VNSTOCK_API_KEY", "")
if _api_key:
    change_api_key(_api_key)


class _RateLimiter:
    """Sliding-window rate limiter. Blocks until a call slot is available."""

    def __init__(self, calls_per_minute: int = 55):
        self._limit = calls_per_minute
        self._window = 60.0
        self._timestamps: deque[float] = deque()
        self._lock = threading.Lock()

    def acquire(self):
        with self._lock:
            now = time.monotonic()
            while self._timestamps and now - self._timestamps[0] >= self._window:
                self._timestamps.popleft()

            if len(self._timestamps) >= self._limit:
                sleep_for = self._window - (now - self._timestamps[0])
                log.debug("Rate limit reached, sleeping %.2fs", sleep_for)
                time.sleep(max(sleep_for, 0))

            self._timestamps.append(time.monotonic())


_limiter = _RateLimiter(calls_per_minute=55)


def get_all_symbols() -> list[dict]:
    """Get all stock symbols from HOSE and HNX exchanges."""
    log.debug("Fetching all symbols")
    _limiter.acquire()
    stock = Vnstock().stock(symbol="VN30F1M", source="VCI")
    df = stock.listing.symbols_by_exchange()
    df = df[df["exchange"].isin(["HOSE", "HNX"])]
    symbols = df[["symbol", "exchange"]].to_dict(orient="records")
    log.info("Fetched %d symbols", len(symbols))
    return symbols


def get_trading_history(symbol: str, days: int = 100) -> list[dict]:
    """Get daily OHLCV history for a symbol."""
    log.debug("Fetching trading history: symbol=%s days=%d", symbol, days)
    _limiter.acquire()
    stock = Vnstock().stock(symbol=symbol, source="VCI")
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    df = stock.quote.history(start=start, end=end)
    return df.to_dict(orient="records")


def get_intraday(symbol: str) -> list[dict]:
    """Get intraday snapshots for a symbol."""
    log.debug("Fetching intraday: symbol=%s", symbol)
    _limiter.acquire()
    stock = Vnstock().stock(symbol=symbol, source="VCI")
    df = stock.quote.intraday()
    return df.to_dict(orient="records")


async def run_full_crawl(history_days: int = 60):
    """Crawl all symbols and persist to DB."""
    from db.connection import init_pool, close_pool
    from crawler.db_writer import write_symbols, write_trading_history, write_stock_metrics, write_intraday

    await init_pool()
    today = date.today()

    try:
        symbols = get_all_symbols()
        await write_symbols(symbols)
        log.info("run_full_crawl: processing %d symbols", len(symbols))

        for i, item in enumerate(symbols):
            symbol = item["symbol"]
            log.info("[%d/%d] Crawling %s", i + 1, len(symbols), symbol)

            history_rows = get_trading_history(symbol, days=history_days)
            if not history_rows:
                log.warning("No history for %s, skipping", symbol)
                continue

            await write_trading_history(symbol, history_rows)

            current_price = float(history_rows[-1]["close"])
            history_sessions = len(history_rows)
            last20 = history_rows[-20:]
            gtgd20 = sum(r["close"] * r["volume"] for r in last20) / len(last20)

            await write_stock_metrics(
                symbol=symbol,
                current_price=current_price,
                gtgd20=gtgd20,
                history_sessions=history_sessions,
                metrics_date=today,
            )

            intraday_rows = get_intraday(symbol)
            if intraday_rows:
                await write_intraday(symbol, today, intraday_rows)

        log.info("run_full_crawl: done")
    finally:
        await close_pool()
