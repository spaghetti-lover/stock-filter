import asyncio

from fastmcp import FastMCP

from infrastructure.market_data.data import get_all_symbols, get_trading_history, get_intraday

mcp = FastMCP(name="data")


@mcp.tool
async def list_symbols(exchange: str = "") -> dict:
    """List all stock symbols from HOSE and HNX exchanges. Returns symbol and exchange for each stock."""
    exchange_filter = exchange.upper() if exchange else ""
    symbols = await asyncio.to_thread(get_all_symbols)
    if exchange_filter:
        symbols = [s for s in symbols if s["exchange"] == exchange_filter]
    return {"total": len(symbols), "symbols": symbols}


@mcp.tool
async def trading_history(symbol: str, days: int = 30) -> dict:
    """Get daily OHLCV (open, high, low, close, volume) history for a stock symbol.

    Args:
        symbol: Stock symbol, e.g. VCB
        days: Number of calendar days to look back (default 30)
    """
    rows = await asyncio.to_thread(get_trading_history, symbol.upper(), days)
    if not rows:
        return {"error": f"No trading history found for {symbol}"}
    return {"symbol": symbol, "sessions": len(rows), "history": rows}


@mcp.tool
async def intraday_data(symbol: str) -> dict:
    """Get today's intraday tick data (time, price, volume) for a stock symbol.

    Only available during trading hours 9:00-15:00 Vietnam time.

    Args:
        symbol: Stock symbol, e.g. VCB
    """
    rows = await asyncio.to_thread(get_intraday, symbol.upper())
    if not rows:
        return {"error": f"No intraday data for {symbol} (market may be closed)"}
    return {"symbol": symbol, "ticks": len(rows), "data": rows}


@mcp.tool
async def stock_price(symbol: str) -> dict:
    """Get the current (latest closing) price and key metrics for a stock.

    Returns price, 30-day high/low, average volume, and GTGD20.

    Args:
        symbol: Stock symbol, e.g. VCB
    """
    rows = await asyncio.to_thread(get_trading_history, symbol.upper(), 30)
    if not rows:
        return {"error": f"No data found for {symbol}"}
    latest = rows[-1]
    last_20 = rows[-20:] if len(rows) >= 20 else rows
    gtgd20 = sum(r["close"] * 1000 * r["volume"] for r in last_20) / len(last_20)
    avg_volume = sum(r["volume"] for r in last_20) / len(last_20)
    return {
        "symbol": symbol,
        "current_price": latest["close"],
        "price_unit": "thousand VND",
        "latest_date": str(latest.get("time")),
        "high_30d": max(r["high"] for r in rows),
        "low_30d": min(r["low"] for r in rows),
        "avg_volume_20d": round(avg_volume),
        "gtgd20_billion": round(gtgd20 / 1e9, 2),
    }


@mcp.tool
async def compare_stocks(symbols: str) -> dict | list:
    """Compare key metrics for 2-5 stock symbols side by side: price, GTGD20, 30-day high/low.

    Args:
        symbols: Comma-separated list of 2-5 stock symbols, e.g. VCB,TCB,MBB
    """
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    if len(symbol_list) < 2:
        return {"error": "Provide at least 2 symbols separated by commas"}
    if len(symbol_list) > 5:
        return {"error": "Maximum 5 symbols for comparison"}
    results = []
    for sym in symbol_list:
        rows = await asyncio.to_thread(get_trading_history, sym, 30)
        if not rows:
            results.append({"symbol": sym, "error": "no data"})
            continue
        latest = rows[-1]
        last_20 = rows[-20:] if len(rows) >= 20 else rows
        gtgd20 = sum(r["close"] * 1000 * r["volume"] for r in last_20) / len(last_20)
        results.append({
            "symbol": sym,
            "current_price": latest["close"],
            "high_30d": max(r["high"] for r in rows),
            "low_30d": min(r["low"] for r in rows),
            "gtgd20_billion": round(gtgd20 / 1e9, 2),
            "sessions": len(rows),
        })
    return results


if __name__ == "__main__":
    mcp.run(transport="stdio")
