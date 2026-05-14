import asyncio

from fastmcp import FastMCP

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


if __name__ == "__main__":
    mcp.run(transport="stdio")
