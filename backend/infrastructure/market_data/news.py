"""News fetching using vnstock_news library + site-search scrapers."""

import html as _html
import re
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

from vnstock_news import Crawler
from vnstock_news.trending.analyzer import TrendingAnalyzer

# Sites with confirmed working RSS feeds (probed against vnstock_news 4.x).
_RSS_SITES: tuple[str, ...] = (
    "vietstock",
    "cafebiz",
    "vnexpress",
    "tuoitre",
)
_PRIMARY_SITE = "vietstock"

_UA = "Mozilla/5.0 (compatible; stock-filter/1.0)"
_HTTP_TIMEOUT = 10.0


def _http_get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    return urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT).read().decode("utf-8", "ignore")


def _clean_title(s: str) -> str:
    return _html.unescape(s).strip()


def _cafef_site_search(kw: str, limit: int) -> list[dict]:
    """Scrape https://cafef.vn/tim-kiem.chn — financial news focus."""
    try:
        url = f"https://cafef.vn/tim-kiem.chn?keywords={urllib.parse.quote(kw)}"
        html = _http_get(url)
        start = html.find('<div class="timeline list-bytags"')
        if start == -1:
            return []
        block = html[start:start + 200_000]
        pat = re.compile(
            r'<h3 class="titlehidden">\s*<a\s+href="([^"]+)"\s+title="([^"]+)"',
            re.S,
        )
        out, seen = [], set()
        for m in pat.finditer(block):
            href, title = m.group(1), m.group(2)
            if href in seen:
                continue
            seen.add(href)
            full = href if href.startswith("http") else "https://cafef.vn" + href
            out.append({"url": full, "title": _clean_title(title), "source": "cafef"})
            if len(out) >= limit:
                break
        return out
    except Exception:
        return []


def _vnexpress_site_search(kw: str, limit: int) -> list[dict]:
    """Scrape https://timkiem.vnexpress.net/ — general news, broad coverage."""
    try:
        url = f"https://timkiem.vnexpress.net/?q={urllib.parse.quote(kw)}"
        html = _http_get(url)
        pat = re.compile(
            r'<a[^>]+href="(https://vnexpress\.net/[^"]+\.html)"[^>]+title="([^"]+)"',
            re.S,
        )
        kw_lower = kw.lower()
        out, seen = [], set()
        for m in pat.finditer(html):
            href, title = m.group(1), m.group(2)
            if href in seen:
                continue
            seen.add(href)
            title_clean = _clean_title(title)
            # nav menu items have no keyword in title — filter
            if kw_lower not in title_clean.lower():
                continue
            out.append({"url": href, "title": title_clean, "source": "vnexpress"})
            if len(out) >= limit:
                break
        return out
    except Exception:
        return []


def _vietnamnet_site_search(kw: str, limit: int) -> list[dict]:
    """Scrape https://vietnamnet.vn/tim-kiem — best title yield in probe (20 FPT hits)."""
    try:
        url = f"https://vietnamnet.vn/tim-kiem?q={urllib.parse.quote(kw)}"
        html = _http_get(url)
        pat = re.compile(r'<a[^>]+href="([^"]+)"[^>]+title="([^"]+)"', re.S)
        kw_lower = kw.lower()
        out, seen = [], set()
        for m in pat.finditer(html):
            href, title = m.group(1), m.group(2)
            title_clean = _clean_title(title)
            if kw_lower not in title_clean.lower():
                continue
            if href in seen:
                continue
            seen.add(href)
            full = href if href.startswith("http") else "https://vietnamnet.vn" + href
            out.append({"url": full, "title": title_clean, "source": "vietnamnet"})
            if len(out) >= limit:
                break
        return out
    except Exception:
        return []


def _plo_site_search(kw: str, limit: int) -> list[dict]:
    """Scrape https://plo.vn/tim-kiem.html."""
    try:
        url = f"https://plo.vn/tim-kiem.html?q={urllib.parse.quote(kw)}"
        html = _http_get(url)
        pat = re.compile(r'<a[^>]+href="([^"]+)"[^>]+title="([^"]+)"', re.S)
        kw_lower = kw.lower()
        out, seen = [], set()
        for m in pat.finditer(html):
            href, title = m.group(1), m.group(2)
            title_clean = _clean_title(title)
            if kw_lower not in title_clean.lower():
                continue
            if href in seen:
                continue
            seen.add(href)
            full = href if href.startswith("http") else "https://plo.vn" + href
            out.append({"url": full, "title": title_clean, "source": "plo"})
            if len(out) >= limit:
                break
        return out
    except Exception:
        return []


_SEARCH_SCRAPERS = (
    _cafef_site_search,
    _vnexpress_site_search,
    _vietnamnet_site_search,
    _plo_site_search,
)


def _get_desc(article: dict) -> str:
    """RSS feeds expose summary under different keys: `short_description`
    (vietstock, cafebiz) vs `description` (vnexpress, tuoitre)."""
    return article.get("short_description") or article.get("description") or ""


def _extract(article: dict, site: str | None = None) -> dict:
    row = {
        "title": article.get("title", ""),
        "short_description": _get_desc(article),
        "url": article.get("url", ""),
        "publish_time": str(article.get("publish_time", "")),
        "author": article.get("author", ""),
    }
    if site:
        row["source"] = site
    return row


def _fetch_feed(site: str, limit_per_feed: int) -> tuple[str, list[dict]]:
    try:
        crawler = Crawler(site_name=site)
        return site, crawler.get_articles_from_feed(limit_per_feed=limit_per_feed)
    except Exception:
        return site, []


def _fetch_all_feeds(limit_per_feed: int, sites: tuple[str, ...] = _RSS_SITES) -> list[tuple[str, dict]]:
    flat: list[tuple[str, dict]] = []
    with ThreadPoolExecutor(max_workers=len(sites)) as pool:
        futures = [pool.submit(_fetch_feed, s, limit_per_feed) for s in sites]
        for fut in as_completed(futures):
            site, arts = fut.result()
            for a in arts:
                flat.append((site, a))
    return flat


def _rss_keyword_scan(keyword: str, limit: int) -> list[dict]:
    """Fallback for general/sector terms that may not surface via site-search."""
    keyword_lower = keyword.lower()
    seen: set[str] = set()
    out: list[dict] = []
    for site, article in _fetch_all_feeds(limit_per_feed=50):
        url = article.get("url", "")
        if not url or url in seen:
            continue
        title = article.get("title", "")
        desc = _get_desc(article)
        if keyword_lower in title.lower() or keyword_lower in desc.lower():
            seen.add(url)
            out.append(_extract(article, site))
            if len(out) >= limit:
                break
    return out


def search_news(keyword: str, limit: int = 10) -> list[dict]:
    """Search news by keyword.

    Primary path: fan out across cafef/vnexpress/vietnamnet/plo HTTP site-search
    endpoints in parallel, dedupe by URL. Returns ticker-aware hits for queries
    like 'FPT', 'DNSE', 'Vietcombank'.

    Fallback: if site-search yields nothing (sector terms like 'ngân hàng' may
    miss strict title match), scan the 4 RSS feeds for keyword in title/desc.
    """
    seen: set[str] = set()
    out: list[dict] = []
    with ThreadPoolExecutor(max_workers=len(_SEARCH_SCRAPERS)) as pool:
        futures = [pool.submit(fn, keyword, limit) for fn in _SEARCH_SCRAPERS]
        for fut in as_completed(futures):
            for row in fut.result():
                if row["url"] in seen:
                    continue
                seen.add(row["url"])
                out.append(row)
                if len(out) >= limit:
                    return out
    if not out:
        return _rss_keyword_scan(keyword, limit)
    return out


def get_stock_news(symbol: str, limit: int = 10) -> list[dict]:
    """Fetch recent news mentioning a stock symbol. Routes through `search_news`."""
    return search_news(symbol.upper(), limit)


def get_market_news(limit: int = 10) -> list[dict]:
    """Fetch latest market/financial news from the primary VietStock RSS."""
    crawler = Crawler(site_name=_PRIMARY_SITE)
    articles = crawler.get_articles_from_feed(limit_per_feed=limit)
    return [_extract(a) for a in articles[:limit]]


def get_trending_topics(top_n: int = 20) -> dict[str, int]:
    """Extract trending n-gram phrases across all supported RSS feeds."""
    analyzer = TrendingAnalyzer(min_token_length=3)
    for _site, article in _fetch_all_feeds(limit_per_feed=50):
        title = article.get("title", "")
        desc = _get_desc(article)
        text = f"{title} {desc}".strip()
        if text:
            analyzer.update_trends(text, ngram_range=[2, 3, 4, 5])
    return analyzer.get_top_trends(top_n=top_n)
