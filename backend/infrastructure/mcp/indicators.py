import asyncio
import json

from fastmcp import FastMCP

from infrastructure.market_data.charts import (
    SUPPORTED_CHART_TYPES,
    SUPPORTED_OSCILLATORS,
    SUPPORTED_OVERLAYS,
    build_chart,
)
from infrastructure.market_data.data import get_trading_history
from infrastructure.market_data.indicators import compute_indicator

mcp = FastMCP(name="indicators")


_SUPPORTED = (
    "close_50_sma", "close_200_sma", "close_10_ema",
    "macd", "macds", "macdh",
    "rsi",
    "boll", "boll_ub", "boll_lb",
    "atr", "vwma",
)


@mcp.tool
async def get_ohlcv(symbol: str, days: int = 120) -> dict:
    """Get daily OHLCV history for a symbol with a wide default window suited to technical analysis.

    Args:
        symbol: Stock symbol, e.g. VCB
        days: Number of calendar days to look back (default 120)
    """
    rows = await asyncio.to_thread(get_trading_history, symbol.upper(), days)
    if not rows:
        return {"error": f"No OHLCV data for {symbol}"}
    return {"symbol": symbol.upper(), "sessions": len(rows), "history": rows}


@mcp.tool
async def get_indicator(symbol: str, indicator: str, days: int = 120) -> dict:
    """Compute one technical indicator for a symbol. Call once per indicator name.

    Supported indicators: close_50_sma, close_200_sma, close_10_ema,
    macd, macds, macdh, rsi, boll, boll_ub, boll_lb, atr, vwma.

    Returns the last 20 trading sessions as {time, value} pairs.

    Args:
        symbol: Stock symbol, e.g. VCB
        indicator: One of the supported indicator names above
        days: Calendar days of OHLCV history to load (default 120; SMA200 needs >=200)
    """
    name = indicator.strip().lower()
    if name not in _SUPPORTED:
        return {"error": f"unsupported indicator: {indicator}", "supported": list(_SUPPORTED)}
    try:
        return await asyncio.to_thread(compute_indicator, symbol, name, days)
    except (ValueError, ConnectionError, ConnectionResetError, AttributeError) as e:
        return {"error": str(e)}


@mcp.tool
async def make_chart(
    symbol: str,
    chart_type: str = "candlestick",
    indicators: list[str] | str | None = None,
    days: int = 120,
) -> dict:
    """Build a chart payload (OHLCV + indicators) for rendering in the chat UI.

    Use this whenever the user asks for a chart, plot, graph, "biểu đồ", "vẽ" or
    visual analysis. After calling, embed the returned JSON in your reply inside
    a fenced code block tagged `chart`, like:

        ```chart
        {"symbol": "VCB", ...}
        ```

    The frontend detects this fence and renders an interactive chart.

    Args:
        symbol: Stock symbol, e.g. VCB.
        chart_type: One of candlestick, line, area. Default candlestick.
        indicators: List of indicator specs. Overlays on the price pane:
            sma:LENGTH (e.g. sma:20), ema:LENGTH, vwma:LENGTH, bbands:LENGTH:STD.
            Oscillators (rendered in their own pane below price):
            rsi:LENGTH, macd:FAST:SLOW:SIGNAL (params optional).
            Example: ["sma:20", "sma:50", "bbands:20:2", "rsi:14", "macd"].
        days: Calendar days of history (default 120; use >= 280 for SMA200).
    """
    if chart_type.lower() not in SUPPORTED_CHART_TYPES:
        return {
            "error": f"unsupported chart_type: {chart_type}",
            "supported_chart_types": list(SUPPORTED_CHART_TYPES),
        }
    if isinstance(indicators, str):
        s = indicators.strip()
        if not s:
            indicators_list: list[str] = []
        elif s.startswith("["):
            try:
                parsed = json.loads(s)
            except json.JSONDecodeError as e:
                return {"error": f"indicators is not valid JSON: {e}"}
            if not isinstance(parsed, list) or not all(isinstance(x, str) for x in parsed):
                return {"error": "indicators must be a list of strings"}
            indicators_list = parsed
        else:
            indicators_list = [p.strip() for p in s.split(",") if p.strip()]
    else:
        indicators_list = indicators or []
    try:
        return await asyncio.to_thread(
            build_chart, symbol, chart_type, indicators_list, days
        )
    except (ValueError, ConnectionError, ConnectionResetError, AttributeError, KeyError) as e:
        return {
            "error": str(e),
            "supported_overlays": list(SUPPORTED_OVERLAYS),
            "supported_oscillators": list(SUPPORTED_OSCILLATORS),
        }


if __name__ == "__main__":
    mcp.run(transport="stdio")
