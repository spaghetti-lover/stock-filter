"""News fetching using vnstock_news library."""

from vnstock_news import Crawler


def get_stock_news(symbol: str, limit: int = 10) -> list[dict]:
    """Fetch recent news articles mentioning a stock symbol from CafeF RSS."""
    symbol_upper = symbol.upper()
    crawler = Crawler(site_name="cafef")
    articles = crawler.get_articles_from_feed(limit_per_feed=50)

    filtered = []
    for article in articles:
        title = article.get("title", "")
        desc = article.get("short_description", "")
        if symbol_upper in title.upper() or symbol_upper in desc.upper():
            filtered.append({
                "title": title,
                "short_description": desc,
                "url": article.get("url", ""),
                "publish_time": str(article.get("publish_time", "")),
                "author": article.get("author", ""),
            })

    return filtered[:limit]


def get_market_news(limit: int = 10) -> list[dict]:
    """Fetch latest market/financial news from CafeF RSS."""
    crawler = Crawler(site_name="cafef")
    articles = crawler.get_articles_from_feed(limit_per_feed=limit)

    return [
        {
            "title": a.get("title", ""),
            "short_description": a.get("short_description", ""),
            "url": a.get("url", ""),
            "publish_time": str(a.get("publish_time", "")),
            "author": a.get("author", ""),
        }
        for a in articles[:limit]
    ]
