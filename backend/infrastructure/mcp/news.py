import asyncio

from fastmcp import FastMCP

from infrastructure.market_data.news import get_stock_news, get_market_news, search_news as _search_news, get_trending_topics

mcp = FastMCP(name="news")


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
