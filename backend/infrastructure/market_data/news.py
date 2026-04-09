"""News fetching using vnstock_news library."""

from vnstock_news import Crawler
from vnstock_news.trending.analyzer import TrendingAnalyzer

# Sites with confirmed RSS support for financial/stock news
_PRIMARY_SITE = "vietstock"
_SEARCH_SITES = ("vietstock", "cafebiz")


def _extract(article: dict) -> dict:
    return {
        "title": article.get("title", ""),
        "short_description": article.get("short_description", ""),
        "url": article.get("url", ""),
        "publish_time": str(article.get("publish_time", "")),
        "author": article.get("author", ""),
    }


def get_stock_news(symbol: str, limit: int = 10) -> list[dict]:
    """Fetch recent news articles mentioning a stock symbol from VietStock RSS."""
    symbol_upper = symbol.upper()
    crawler = Crawler(site_name=_PRIMARY_SITE)
    articles = crawler.get_articles_from_feed(limit_per_feed=50)

    filtered = []
    for article in articles:
        title = article.get("title", "")
        desc = article.get("short_description", "")
        if symbol_upper in title.upper() or symbol_upper in desc.upper():
            filtered.append(_extract(article))

    return filtered[:limit]


def get_market_news(limit: int = 10) -> list[dict]:
    """Fetch latest market/financial news from VietStock RSS."""
    crawler = Crawler(site_name=_PRIMARY_SITE)
    articles = crawler.get_articles_from_feed(limit_per_feed=limit)
    return [_extract(a) for a in articles[:limit]]


def search_news(keyword: str, limit: int = 10) -> list[dict]:
    """Search news by keyword across VietStock and CafeBiz RSS feeds.

    Useful for sector queries (e.g. "ngân hàng", "bất động sản"),
    company full names, or any topic beyond a ticker symbol.
    """
    keyword_lower = keyword.lower()
    results = []
    seen_urls: set[str] = set()

    for site in _SEARCH_SITES:
        try:
            crawler = Crawler(site_name=site)
            articles = crawler.get_articles_from_feed(limit_per_feed=50)
        except Exception:
            continue

        for article in articles:
            url = article.get("url", "")
            if url in seen_urls:
                continue
            title = article.get("title", "")
            desc = article.get("short_description", "")
            if keyword_lower in title.lower() or keyword_lower in desc.lower():
                seen_urls.add(url)
                row = _extract(article)
                row["source"] = site
                results.append(row)

    return results[:limit]


def get_trending_topics(top_n: int = 20) -> dict[str, int]:
    """Extract trending n-gram phrases from recent VietStock news headlines.

    Uses TrendingAnalyzer to find the most frequently appearing
    2-5 word phrases in today's financial news.
    """
    crawler = Crawler(site_name=_PRIMARY_SITE)
    articles = crawler.get_articles_from_feed(limit_per_feed=50)

    analyzer = TrendingAnalyzer(min_token_length=3)
    for article in articles:
        title = article.get("title", "")
        desc = article.get("short_description", "")
        text = f"{title} {desc}".strip()
        if text:
            analyzer.update_trends(text, ngram_range=[2, 3, 4, 5])

    return analyzer.get_top_trends(top_n=top_n)
