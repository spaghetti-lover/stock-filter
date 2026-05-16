import asyncio

from fastmcp import FastMCP

from infrastructure.market_data.news import get_stock_news, get_market_news, search_news as _search_news, get_trending_topics

mcp = FastMCP(name="news")


@mcp.tool
async def stock_news(symbol: str, limit: int = 10) -> dict:
    """Fetch recent news mentioning a stock symbol via parallel HTTP site-search across CafeF, VnExpress, VietNamNet, PLO.

    Works for tickers (FPT, DNSE, VCB), company names (Vietcombank), or any keyword.
    Falls back to RSS scan (VietStock, CafeBiz, VnExpress, Tuoi Tre) if site-search yields nothing.

    Args:
        symbol: Stock symbol or keyword, e.g. VCB
        limit: Maximum number of articles to return (default 10)
    """
    articles = await asyncio.to_thread(get_stock_news, symbol.upper(), limit)
    if not articles:
        return {"error": f"No recent news found for {symbol}"}
    return {"symbol": symbol, "count": len(articles), "articles": articles}


@mcp.tool
async def market_news(limit: int = 10) -> dict:
    """Fetch the latest general market and financial news from VietStock RSS feed.

    Args:
        limit: Maximum number of articles to return (default 10)
    """
    articles = await asyncio.to_thread(get_market_news, limit)
    if not articles:
        return {"error": "No market news available"}
    return {"count": len(articles), "articles": articles}


@mcp.tool
async def search_news(keyword: str, limit: int = 10) -> dict:
    """Search recent news by keyword via parallel HTTP site-search across CafeF, VnExpress, VietNamNet, PLO.

    Primary path: 4-site parallel scrape, dedupes by URL. Works for tickers
    (FPT, DNSE, DSE, VCB), company names, and proper nouns.
    Fallback: if site-search returns 0 (typical for broad sector terms like
    'ngân hàng'), scans VietStock/CafeBiz/VnExpress/Tuoi Tre RSS feeds.

    Each result has `url`, `title`, `source`.

    Args:
        keyword: Search keyword or phrase, e.g. 'FPT' or 'ngân hàng'
        limit: Maximum number of articles to return (default 10)
    """
    articles = await asyncio.to_thread(_search_news, keyword, limit)
    if not articles:
        return {"error": f"No news found for keyword: {keyword}"}
    return {"keyword": keyword, "count": len(articles), "articles": articles}


@mcp.tool
async def trending_topics(top_n: int = 20) -> dict:
    """Get most frequently appearing phrases in today's news across VietStock, CafeBiz, VnExpress, Tuoi Tre.

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
