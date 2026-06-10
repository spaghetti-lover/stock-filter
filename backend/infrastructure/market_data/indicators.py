"""Technical indicators via vnstock_ta.

Each call loads OHLCV through vnstock_data Market and dispatches to the
matching vnstock_ta Indicator method. Returns the last 20 trading sessions
of the requested indicator as a list of {time, value} dicts.
"""

from datetime import datetime, timedelta

import pandas as pd
from vnstock_data import Market
from vnstock_ta import Indicator


_TAIL = 20


def _load_ohlcv(symbol: str, days: int) -> pd.DataFrame:
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    df = Market().equity(symbol).ohlcv(start=start, end=end)
    if df is None or df.empty:
        raise ValueError(f"No OHLCV data for {symbol} in the last {days} days")
    return df.set_index("time")


def _series_to_records(series: pd.Series) -> list[dict]:
    if series is None:
        return []
    tail = series.dropna().tail(_TAIL)
    return [
        {"time": ts.isoformat() if hasattr(ts, "isoformat") else str(ts), "value": float(v)}
        for ts, v in tail.items()
    ]


def compute_indicator(symbol: str, indicator: str, days: int = 120) -> dict:
    """Compute a single indicator for a symbol over the last `days` calendar days.

    Supported indicator names match the trading-agent prompt vocabulary:
        close_50_sma, close_200_sma, close_10_ema,
        macd, macds, macdh,
        rsi,
        boll, boll_ub, boll_lb,
        atr, vwma
    """
    name = indicator.strip().lower()
    df = _load_ohlcv(symbol.upper(), days)
    ind = Indicator(data=df)

    if name == "close_50_sma":
        series = ind.sma(length=50)
    elif name == "close_200_sma":
        series = ind.sma(length=200)
    elif name == "close_10_ema":
        series = ind.ema(length=10)
    elif name in ("macd", "macds", "macdh"):
        macd_df = ind.macd()
        if macd_df is None:
            raise ValueError(f"MACD computation returned no data for {symbol}")
        column = {"macd": "MACD_12_26_9", "macds": "MACDs_12_26_9", "macdh": "MACDh_12_26_9"}[name]
        series = macd_df[column]
    elif name == "rsi":
        series = ind.rsi(length=14)
    elif name in ("boll", "boll_ub", "boll_lb"):
        bb = ind.bbands(length=20, std=2)
        if bb is None:
            raise ValueError(f"Bollinger Bands computation returned no data for {symbol}")
        prefix = {"boll": "BBM", "boll_ub": "BBU", "boll_lb": "BBL"}[name]
        column = next((c for c in bb.columns if c.startswith(prefix + "_")), None)
        if column is None:
            raise ValueError(f"Bollinger Bands column {prefix} not found; got {bb.columns.tolist()}")
        series = bb[column]
    elif name == "atr":
        series = ind.atr(length=14)
    elif name == "vwma":
        series = ind.vwma(length=20)
    else:
        raise ValueError(f"unsupported indicator: {indicator}")

    return {
        "symbol": symbol.upper(),
        "indicator": name,
        "values": _series_to_records(series),
    }
