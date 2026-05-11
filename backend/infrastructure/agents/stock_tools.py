"""FastMCP server exposing stock data tools for all AI agents."""

import asyncio

from fastmcp import FastMCP

from infrastructure.market_data.data import get_all_symbols, get_trading_history, get_intraday
from infrastructure.market_data.news import get_stock_news, get_market_news, search_news as _search_news, get_trending_topics

mcp = FastMCP(name="stock-data")


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


@mcp.tool
async def stock_news(symbol: str, limit: int = 10) -> dict:
    """Fetch recent news articles mentioning a specific stock symbol from CafeF RSS feed.

    Args:
        symbol: Stock symbol, e.g. VCB
        limit: Maximum number of articles to return (default 10)
    """
    articles = await asyncio.to_thread(get_stock_news, symbol.upper(), limit)
    if not articles:
        return {"error": f"No recent news found for {symbol}"}
    return {"symbol": symbol, "count": len(articles), "articles": articles}


@mcp.tool
async def market_news(limit: int = 10) -> dict:
    """Fetch the latest general market and financial news from CafeF RSS feed.

    Args:
        limit: Maximum number of articles to return (default 10)
    """
    articles = await asyncio.to_thread(get_market_news, limit)
    if not articles:
        return {"error": "No market news available"}
    return {"count": len(articles), "articles": articles}


@mcp.tool
async def search_news(keyword: str, limit: int = 10) -> dict:
    """Search recent news by keyword across CafeF and VietStock RSS feeds.

    Useful for sector queries (e.g. 'ngân hàng', 'bất động sản'), company full names, or any topic.

    Args:
        keyword: Search keyword or phrase, e.g. 'ngân hàng' or 'Vietcombank'
        limit: Maximum number of articles to return (default 10)
    """
    articles = await asyncio.to_thread(_search_news, keyword, limit)
    if not articles:
        return {"error": f"No news found for keyword: {keyword}"}
    return {"keyword": keyword, "count": len(articles), "articles": articles}


@mcp.tool
async def trending_topics(top_n: int = 20) -> dict:
    """Get the most frequently appearing phrases in today's financial news headlines from CafeF.

    Returns trending n-gram phrases and their frequency counts.

    Args:
        top_n: Number of top trending phrases to return (default 20)
    """
    trends = await asyncio.to_thread(get_trending_topics, top_n)
    if not trends:
        return {"error": "No trending topics found"}
    return {"top_n": top_n, "trends": trends}


if __name__ == "__main__":
    mcp.run(transport="stdio")
