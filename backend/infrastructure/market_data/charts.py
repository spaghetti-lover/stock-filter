"""Build chart payloads for the chat assistant.

Loads OHLCV via vnstock_data Market, computes the requested overlay/sub-pane
indicators via vnstock_ta, and emits a single JSON-friendly dict the frontend
Recharts renderer can consume directly.
"""

from datetime import datetime, timedelta

import math
import pandas as pd
from vnstock_data import Market
from vnstock_ta import Indicator


SUPPORTED_CHART_TYPES = ("candlestick", "line", "area")

SUPPORTED_OVERLAYS = ("sma", "ema", "bbands", "vwma")
SUPPORTED_OSCILLATORS = ("rsi", "macd")


def _load_ohlcv(symbol: str, days: int) -> pd.DataFrame:
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    df = Market().equity(symbol).ohlcv(start=start, end=end)
    if df is None or df.empty:
        raise ValueError(f"No OHLCV data for {symbol} in the last {days} days")
    return df.set_index("time")


def _safe_float(v) -> float | None:
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if math.isnan(f) or math.isinf(f):
        return None
    return f


def _ohlcv_rows(df: pd.DataFrame) -> list[dict]:
    rows: list[dict] = []
    for ts, row in df.iterrows():
        rows.append({
            "time": ts.isoformat() if hasattr(ts, "isoformat") else str(ts),
            "open": _safe_float(row.get("open")),
            "high": _safe_float(row.get("high")),
            "low": _safe_float(row.get("low")),
            "close": _safe_float(row.get("close")),
            "volume": _safe_float(row.get("volume")),
        })
    return rows


def _series_values(series: pd.Series) -> list[float | None]:
    return [_safe_float(v) for v in series.tolist()]


def _parse_spec(spec: str) -> tuple[str, dict]:
    """Parse strings like 'sma:20', 'ema:50', 'bbands:20:2', 'rsi:14', 'macd:12:26:9'."""
    parts = spec.strip().lower().split(":")
    name = parts[0]
    params = parts[1:]
    if name == "sma":
        return name, {"length": int(params[0]) if params else 20}
    if name == "ema":
        return name, {"length": int(params[0]) if params else 12}
    if name == "vwma":
        return name, {"length": int(params[0]) if params else 20}
    if name == "bbands":
        return name, {
            "length": int(params[0]) if len(params) >= 1 else 20,
            "std": float(params[1]) if len(params) >= 2 else 2.0,
        }
    if name == "rsi":
        return name, {"length": int(params[0]) if params else 14}
    if name == "macd":
        return name, {
            "fast": int(params[0]) if len(params) >= 1 else 12,
            "slow": int(params[1]) if len(params) >= 2 else 26,
            "signal": int(params[2]) if len(params) >= 3 else 9,
        }
    raise ValueError(f"unsupported indicator spec: {spec}")


def _compute_indicator(ind: Indicator, name: str, params: dict) -> dict:
    """Return {kind: 'overlay'|'oscillator', series: {label: [values...]}}."""
    if name == "sma":
        s = ind.sma(length=params["length"])
        return {"kind": "overlay", "name": f"SMA{params['length']}",
                "series": {f"SMA{params['length']}": _series_values(s)}}
    if name == "ema":
        s = ind.ema(length=params["length"])
        return {"kind": "overlay", "name": f"EMA{params['length']}",
                "series": {f"EMA{params['length']}": _series_values(s)}}
    if name == "vwma":
        s = ind.vwma(length=params["length"])
        return {"kind": "overlay", "name": f"VWMA{params['length']}",
                "series": {f"VWMA{params['length']}": _series_values(s)}}
    if name == "bbands":
        bb = ind.bbands(length=params["length"], std=params["std"])
        if bb is None or bb.empty:
            raise ValueError("BBANDS produced no data")

        def _bb_col(prefix: str) -> str:
            col = next((c for c in bb.columns if c.startswith(prefix + "_")), None)
            if col is None:
                raise ValueError(f"Bollinger Bands column {prefix} not found; got {bb.columns.tolist()}")
            return col

        return {
            "kind": "overlay",
            "name": f"BB({params['length']},{params['std']})",
            "series": {
                "BB_upper": _series_values(bb[_bb_col("BBU")]),
                "BB_middle": _series_values(bb[_bb_col("BBM")]),
                "BB_lower": _series_values(bb[_bb_col("BBL")]),
            },
        }
    if name == "rsi":
        s = ind.rsi(length=params["length"])
        return {"kind": "oscillator", "name": f"RSI{params['length']}", "pane": "rsi",
                "series": {f"RSI{params['length']}": _series_values(s)}}
    if name == "macd":
        m = ind.macd(fast=params["fast"], slow=params["slow"], signal=params["signal"])
        if m is None or m.empty:
            raise ValueError("MACD produced no data")
        sfx = f"_{params['fast']}_{params['slow']}_{params['signal']}"
        return {
            "kind": "oscillator",
            "name": f"MACD({params['fast']},{params['slow']},{params['signal']})",
            "pane": "macd",
            "series": {
                "MACD": _series_values(m[f"MACD{sfx}"]),
                "signal": _series_values(m[f"MACDs{sfx}"]),
                "histogram": _series_values(m[f"MACDh{sfx}"]),
            },
        }
    raise ValueError(f"unsupported indicator: {name}")


def build_chart(
    symbol: str,
    chart_type: str = "candlestick",
    indicators: list[str] | None = None,
    days: int = 120,
) -> dict:
    """Build a chart payload for the chat assistant.

    Args:
        symbol: Stock symbol.
        chart_type: One of SUPPORTED_CHART_TYPES.
        indicators: Specs like ["sma:20", "sma:50", "bbands:20:2", "rsi:14", "macd"].
        days: Calendar days of OHLCV history (SMA200 needs >= 280).
    """
    chart_type = chart_type.strip().lower()
    if chart_type not in SUPPORTED_CHART_TYPES:
        raise ValueError(
            f"unsupported chart_type: {chart_type}. Use one of {SUPPORTED_CHART_TYPES}"
        )

    df = _load_ohlcv(symbol.upper(), days)
    ind = Indicator(data=df)

    overlays: list[dict] = []
    oscillators: list[dict] = []
    for spec in indicators or []:
        name, params = _parse_spec(spec)
        result = _compute_indicator(ind, name, params)
        if result["kind"] == "overlay":
            overlays.append(result)
        else:
            oscillators.append(result)

    return {
        "symbol": symbol.upper(),
        "chart_type": chart_type,
        "days": days,
        "ohlcv": _ohlcv_rows(df),
        "overlays": overlays,
        "oscillators": oscillators,
    }
