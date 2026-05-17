from dataclasses import asdict
from datetime import datetime, timedelta, timezone

from fastmcp import FastMCP

from infrastructure.container import get_discussion_crawl_usecase

mcp = FastMCP(name="discussions")


def _posts_to_dicts(posts) -> list[dict]:
    out = []
    for p in posts:
        d = asdict(p)
        d["posted_at"] = p.posted_at.isoformat()
        d["ticker_symbols"] = list(p.ticker_symbols)
        out.append(d)
    return out


@mcp.tool
async def discussion_by_ticker(symbol: str, limit: int = 20, days: int = 7) -> dict:
    """Recent community-forum posts mentioning a ticker (f319.com).

    Searches a local cache of posts scraped from f319.com Vietnamese stock
    forum. Posts are tagged with their tickers via whitelist regex.

    Args:
        symbol: Stock symbol, e.g. VCB, FPT
        limit: Max posts to return (default 20)
        days: Lookback window in days (default 7)
    """
    since = datetime.now(tz=timezone.utc) - timedelta(days=days)
    repo = get_discussion_crawl_usecase().repo
    posts = await repo.search_by_ticker(symbol.upper(), limit, since)
    if not posts:
        return {"error": f"No discussion posts found for {symbol} in last {days} days"}
    return {
        "symbol": symbol.upper(),
        "days": days,
        "count": len(posts),
        "posts": _posts_to_dicts(posts),
    }


@mcp.tool
async def discussion_search(keyword: str, limit: int = 20, days: int = 7) -> dict:
    """Full-text search community-forum posts (f319.com) by keyword.

    Uses Postgres tsvector ('simple' config) for substring/word matching.
    Good for themes, company names, sector terms, or any free text.

    Args:
        keyword: Search term, e.g. 'cổ tức', 'FPT'
        limit: Max posts to return (default 20)
        days: Lookback window in days (default 7)
    """
    since = datetime.now(tz=timezone.utc) - timedelta(days=days)
    repo = get_discussion_crawl_usecase().repo
    posts = await repo.search_by_keyword(keyword, limit, since)
    if not posts:
        return {"error": f"No discussion posts matched '{keyword}' in last {days} days"}
    return {
        "keyword": keyword,
        "days": days,
        "count": len(posts),
        "posts": _posts_to_dicts(posts),
    }
