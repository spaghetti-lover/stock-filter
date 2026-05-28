import time
import threading
from collections import deque
from datetime import datetime, timedelta

from vnstock_data import Reference, Market, Insights
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
        while True:
            with self._lock:
                now = time.monotonic()
                while self._timestamps and now - self._timestamps[0] >= self._window:
                    self._timestamps.popleft()

                if len(self._timestamps) < self._limit:
                    self._timestamps.append(time.monotonic())
                    return

                sleep_for = self._window - (now - self._timestamps[0]) + 0.05
            log.debug("Rate limit reached, sleeping %.2fs", sleep_for)
            time.sleep(max(sleep_for, 0))


_limiter = _RateLimiter(calls_per_minute=450)

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


def get_vnindex_history(days: int = 40) -> list[dict]:
    """Get daily OHLCV for VNINDEX (40-day window gives headroom for 20-session MA)."""
    log.debug("Fetching VNINDEX history: days=%d", days)
    _limiter.acquire()
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    try:
        df = Market().equity("VNINDEX").ohlcv(start=start, end=end)
    except (ValueError, ConnectionResetError, ConnectionError):
        log.debug("No VNINDEX history available")
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


def get_foreign_flow(symbol: str, days: int = 10) -> list[dict]:
    """Get foreign buy/sell value per session (last N calendar days → ~5 trading sessions)."""
    log.debug("Fetching foreign_flow: symbol=%s days=%d", symbol, days)
    _limiter.acquire()
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    try:
        df = Market().equity(symbol).foreign_flow(start=start, end=end)
    except Exception:
        log.debug("No foreign flow for %s", symbol)
        return []
    return df[["trading_date", "buy_val", "sell_val"]].to_dict(orient="records")


def get_proprietary_flow(symbol: str, days: int = 10) -> list[dict]:
    """Get proprietary (tự doanh) buy/sell value per session."""
    log.debug("Fetching proprietary_flow: symbol=%s days=%d", symbol, days)
    _limiter.acquire()
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    try:
        df = Market().equity(symbol).proprietary_flow(start=start, end=end)
    except Exception:
        log.debug("No proprietary flow for %s", symbol)
        return []
    return df[["trading_date", "buy_val", "sell_val"]].to_dict(orient="records")


def get_market_flow(exchange: str) -> dict[str, dict]:
    """Fetch market-wide net flow (foreign, prop, active) for one exchange.

    Uses the sponsored `Insights().flow.*` APIs (vnstock_data >= 3.2.0),
    which return one row per symbol with pre-aggregated NET values over
    fixed windows (1d, 10d, 1m, 3m, 6m). Replaces ~3×N per-symbol calls
    with 3 market-wide calls per refresh.

    Quirk: `flow.active(...)` is missing its `symbol` column in this
    build; rows are positionally aligned with `flow.foreign(...)` so we
    label them using foreign's symbol series.

    Returns {symbol: {foreign_net_1d, foreign_net_10d, prop_net_1d,
    prop_net_10d, active_net_1d, active_net_10d}}.
    Returns {} on any failure so callers can degrade gracefully.
    """
    log.debug("Fetching market_flow: exchange=%s", exchange)
    out: dict[str, dict] = {}
    try:
        _limiter.acquire()
        df_f = Insights().flow.foreign(exchange=exchange, group_by="stock")
        _limiter.acquire()
        df_p = Insights().flow.proprietary(exchange=exchange, group_by="stock")
        _limiter.acquire()
        df_a = Insights().flow.active(exchange=exchange, group_by="stock")
    except Exception:
        log.debug("Market flow fetch failed for %s", exchange, exc_info=True)
        return {}

    # Active dataframe rows align positionally with foreign — label by foreign's symbol.
    n = min(len(df_f), len(df_p), len(df_a))
    if n == 0 or "symbol" not in df_f.columns:
        return {}

    symbols = df_f["symbol"].iloc[:n].tolist()
    f_1d = df_f["value_1d"].iloc[:n].tolist()
    f_10d = df_f["value_10d"].iloc[:n].tolist()
    p_1d = df_p["value_1d"].iloc[:n].tolist()
    p_10d = df_p["value_10d"].iloc[:n].tolist()
    a_1d = df_a["value_1d"].iloc[:n].tolist()
    a_10d = df_a["value_10d"].iloc[:n].tolist()

    for i, sym in enumerate(symbols):
        out[sym] = {
            "foreign_net_1d": _safe_float(f_1d[i]),
            "foreign_net_10d": _safe_float(f_10d[i]),
            "prop_net_1d": _safe_float(p_1d[i]),
            "prop_net_10d": _safe_float(p_10d[i]),
            "active_net_1d": _safe_float(a_1d[i]),
            "active_net_10d": _safe_float(a_10d[i]),
        }
    log.info("Fetched market_flow for %s: %d symbols", exchange, len(out))
    return out


def _safe_float(v) -> float | None:
    """Convert a pandas/numpy value to float, returning None for NaN/None."""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if f != f:  # NaN check
        return None
    return f
