import time
import threading
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

from vnstock_data import Reference, Market
from logger import get_logger

log = get_logger(__name__)


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


_limiter = _RateLimiter(calls_per_minute=120)

def get_all_symbols() -> list[dict]:
    """Get all stock symbols from HOSE and HNX exchanges."""
    log.debug("Fetching all symbols")
    _limiter.acquire()
    df = Reference().equity.list_by_exchange()
    df = df[df["exchange"].isin(["HOSE", "HNX"])]
    symbols = df[["symbol", "exchange"]].to_dict(orient="records")
    log.info("Fetched %d symbols", len(symbols))
    return symbols


def get_trading_history(symbol: str, days: int = 100) -> list[dict]:
    """Get daily OHLCV history for a symbol."""
    log.debug("Fetching trading history: symbol=%s days=%d", symbol, days)
    _limiter.acquire()
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    try:
        df = Market().equity(symbol).ohlcv(start=start, end=end)
    except (ValueError, ConnectionResetError, ConnectionError):
        log.debug("No trading history for %s", symbol)
        return []
    return df.to_dict(orient="records")


def get_intraday(symbol: str) -> list[dict]:
    """Get intraday snapshots for a symbol."""
    log.debug("Fetching intraday: symbol=%s", symbol)
    _limiter.acquire()
    try:
        df = Market().equity(symbol).intraday()
    except (ValueError, ConnectionResetError, ConnectionError):
        log.debug("No intraday data for %s", symbol)
        return []
    df["time"] = df["time"].dt.time
    return df[["time", "price", "volume"]].to_dict(orient="records")
