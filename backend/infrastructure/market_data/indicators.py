"""Technical indicators via vnstock_ta.

Each call loads OHLCV through vnstock_data Market and dispatches to the
matching vnstock_ta Indicator method. Returns the last 20 trading sessions
of the requested indicator as a list of {time, value} dicts.
"""

import pandas as pd
from vnstock_ta import Indicator

from infrastructure.market_data.data import get_trading_history


_TAIL = 20


def _load_ohlcv(symbol: str, days: int) -> pd.DataFrame:
    # Route through get_trading_history so the as-of clock (backtest
    # look-ahead guard) applies here too — the Technical Analyst must not see
    # bars after the decision date.
    rows = get_trading_history(symbol, days=days)
    if not rows:
        raise ValueError(f"No OHLCV data for {symbol} in the last {days} days")
    df = pd.DataFrame(rows)
    df = df.set_index("time")
    # The API occasionally returns duplicate timestamps; pandas_ta's internal
    # reindex (e.g. in macd()) raises on duplicate labels. Keep the last.
    df = df[~df.index.duplicated(keep="last")].sort_index()
    return df


def _match_column(df: pd.DataFrame, prefix: str) -> str:
    """Return the first column starting with ``prefix``.

    pandas_ta column suffixes vary across versions (e.g. "_20_2" vs
    "_20_2.0"); matching by stable prefix avoids brittle hardcoded names.
    """
    for col in df.columns:
        if str(col).startswith(prefix):
            return str(col)
    raise KeyError(f"no column with prefix {prefix!r} in {list(df.columns)}")


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
        # Match by prefix — pandas_ta column suffixes drift across versions
        # (e.g. "MACD_12_26_9"); prefix is stable.
        prefix = {"macd": "MACD_", "macds": "MACDs_", "macdh": "MACDh_"}[name]
        series = macd_df[_match_column(macd_df, prefix)]
    elif name == "rsi":
        series = ind.rsi(length=14)
    elif name in ("boll", "boll_ub", "boll_lb"):
        bb = ind.bbands(length=20, std=2)
        if bb is None:
            raise ValueError(f"Bollinger Bands computation returned no data for {symbol}")
        # Version-robust: BBM/BBU/BBL prefix (suffix is "_20_2" or "_20_2.0").
        prefix = {"boll": "BBM_", "boll_ub": "BBU_", "boll_lb": "BBL_"}[name]
        series = bb[_match_column(bb, prefix)]
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
