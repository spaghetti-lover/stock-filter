import time
import threading
from collections import deque
from datetime import datetime, timedelta

import pandas as pd
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


def get_smart_money_raw(symbol: str, days: int) -> list[dict]:
    """Per-day foreign + proprietary flow joined with OHLCV-derived GTGD/close.

    Calls Market.equity(symbol).foreign_flow / .proprietary_flow / .ohlcv
    over a window of [today - days*2 calendar days, today] to ensure enough
    trading sessions are returned (vnstock returns trading days only, so the
    calendar window is padded). The result is left-joined on ohlcv `time`
    (the trading-day truth), oldest-first, with total_gtgd ≈ close × volume.

    Sessions where total_gtgd is null or 0 are dropped (per chart spec §10).

    Returns a list of dicts with keys:
      date (YYYY-MM-DD), foreign_buy_value, foreign_sell_value,
      prop_buy_value, prop_sell_value, total_gtgd, close_price.
    Missing flow on a real trading day is filled with 0.
    """
    log.debug("Fetching smart_money_raw: symbol=%s days=%d", symbol, days)
    # Pad the calendar window so we get at least `days` trading sessions back.
    pad = max(int(days * 2), days + 30)
    end_dt = datetime.now()
    start_dt = end_dt - timedelta(days=pad)
    end = end_dt.strftime("%Y-%m-%d")
    start = start_dt.strftime("%Y-%m-%d")

    eq = Market().equity(symbol)

    _limiter.acquire()
    df_ohlcv = eq.ohlcv(start=start, end=end)
    _limiter.acquire()
    df_f = eq.foreign_flow(start=start, end=end)
    _limiter.acquire()
    try:
        df_p = eq.proprietary_flow(start=start, end=end)
    except AttributeError:
        # vnstock_data bug: some symbols return integer columns that fail .str accessor
        log.warning("proprietary_flow unavailable for %s (library bug), skipping", symbol)
        df_p = None

    if df_ohlcv is None or len(df_ohlcv) == 0:
        return []

    o = df_ohlcv[["time", "close", "volume"]].copy()
    o["time"] = pd.to_datetime(o["time"]).dt.normalize()
    # vnstock `close` is in VND×1000 (price quote scale); `volume` is in shares;
    # `foreign_flow.buy_val` is in VND. Normalize so total_gtgd is in VND.
    o["total_gtgd"] = o["close"].astype(float) * 1000.0 * o["volume"].astype(float)

    def _flow_frame(df, prefix: str) -> pd.DataFrame:
        if df is None or len(df) == 0:
            return pd.DataFrame(columns=["time", f"{prefix}_buy_value", f"{prefix}_sell_value"])
        f = df[["time", "buy_val", "sell_val"]].copy()
        f["time"] = pd.to_datetime(f["time"]).dt.normalize()
        f = f.rename(columns={"buy_val": f"{prefix}_buy_value", "sell_val": f"{prefix}_sell_value"})
        return f

    ff = _flow_frame(df_f, "foreign")
    pf = _flow_frame(df_p, "prop")

    merged = o.merge(ff, on="time", how="left").merge(pf, on="time", how="left")
    for col in ("foreign_buy_value", "foreign_sell_value", "prop_buy_value", "prop_sell_value"):
        if col not in merged.columns:
            merged[col] = 0.0
        merged[col] = merged[col].fillna(0.0).astype(float)

    # Drop sessions with no real GTGD (spec §10).
    merged = merged[merged["total_gtgd"].notna() & (merged["total_gtgd"] > 0)]
    merged = merged.sort_values("time", ascending=True).reset_index(drop=True)

    out: list[dict] = []
    # Take the last `days` trading sessions (oldest-first slice).
    if len(merged) > days:
        merged = merged.tail(days).reset_index(drop=True)

    for _, row in merged.iterrows():
        out.append({
            "date": row["time"].strftime("%Y-%m-%d"),
            "foreign_buy_value": float(row["foreign_buy_value"]),
            "foreign_sell_value": float(row["foreign_sell_value"]),
            "prop_buy_value": float(row["prop_buy_value"]),
            "prop_sell_value": float(row["prop_sell_value"]),
            "total_gtgd": float(row["total_gtgd"]),
            "close_price": float(row["close"]),
        })
    log.info("smart_money_raw %s: %d rows", symbol, len(out))
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
