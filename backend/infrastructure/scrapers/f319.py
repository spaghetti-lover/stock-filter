import asyncio
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from domain.entities.discussion_post import DiscussionPost
from infrastructure.scrapers.base import DiscussionScraper, build_http_client
from infrastructure.scrapers.ticker_extractor import extract_tickers
from logger import get_logger

log = get_logger(__name__)

_BASE = "https://f319.com/"
_FORUM_PATH = "forums/thi-truong-chung-khoan.3/"
_THREAD_CONCURRENCY = 5
_REQUEST_DELAY_SEC = 0.3
_BATCH_SIZE = 200
_DATETIME_RE = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})\s*lúc\s*(\d{1,2}):(\d{1,2})")
_VN_TZ = timezone(timedelta(hours=7))


class _Retry(Exception):
    pass


def _parse_dt(title: str) -> datetime | None:
    m = _DATETIME_RE.search(title or "")
    if not m:
        return None
    d, mo, y, h, mi = (int(x) for x in m.groups())
    return datetime(y, mo, d, h, mi, tzinfo=_VN_TZ).astimezone(timezone.utc)


class F319Scraper(DiscussionScraper):
    source = "f319"

    def __init__(self, thread_concurrency: int = _THREAD_CONCURRENCY) -> None:
        self.thread_concurrency = thread_concurrency

    @retry(
        retry=retry_if_exception_type(_Retry),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=20),
        reraise=True,
    )
    async def _get(self, client: httpx.AsyncClient, url: str) -> str:
        resp = await client.get(url)
        if resp.status_code == 403:
            log.warning("f319 %s -> 403 Forbidden, not retrying", url)
            resp.raise_for_status()
        if resp.status_code in (429, 503):
            log.warning("f319 %s -> %d, will retry", url, resp.status_code)
            raise _Retry(f"{resp.status_code}")
        resp.raise_for_status()
        await asyncio.sleep(_REQUEST_DELAY_SEC)
        return resp.text

    async def run(self, repo) -> int:
        cursors = await repo.get_cursors(self.source)
        log.info("f319 starting backfill: %d known thread cursors", len(cursors))

        total_inserted = 0
        async with build_http_client() as client:
            page = 0
            while True:
                page += 1
                url = urljoin(
                    _BASE,
                    _FORUM_PATH if page == 1 else f"{_FORUM_PATH}page-{page}",
                )
                try:
                    html = await self._get(client, url)
                except Exception:
                    log.exception("f319 index page %d failed, stopping", page)
                    break

                thread_urls = self._parse_thread_urls(html)
                if not thread_urls:
                    log.info("f319 index page %d empty, end of forum", page)
                    break

                log.info(
                    "f319 index page %d: %d threads",
                    page, len(thread_urls),
                )

                sem = asyncio.Semaphore(self.thread_concurrency)
                results = await asyncio.gather(
                    *(
                        self._crawl_thread(client, t_url, cursors, sem)
                        for t_url in thread_urls
                    ),
                    return_exceptions=True,
                )

                batch_posts: list[DiscussionPost] = []
                cursor_updates: list[tuple[str, str]] = []
                seen_ext: set[str] = set()
                for r in results:
                    if isinstance(r, BaseException):
                        log.warning("f319 thread error: %s", r)
                        continue
                    posts, new_cursor = r
                    if new_cursor is not None:
                        thread_id, max_post_id = new_cursor
                        cursor_updates.append((thread_id, max_post_id))
                    for p in posts:
                        if p.external_id in seen_ext:
                            continue
                        seen_ext.add(p.external_id)
                        batch_posts.append(p)
                        if len(batch_posts) >= _BATCH_SIZE:
                            total_inserted += await repo.save_posts(batch_posts)
                            batch_posts = []
                if batch_posts:
                    total_inserted += await repo.save_posts(batch_posts)

                for thread_id, max_post_id in cursor_updates:
                    cursors[thread_id] = max_post_id
                    await repo.set_cursor(self.source, max_post_id, thread_id)

                log.info(
                    "f319 page %d done: %d inserts cumulative",
                    page, total_inserted,
                )

        log.info("f319 backfill finished: %d posts inserted", total_inserted)
        return total_inserted

    async def _crawl_thread(
        self,
        client: httpx.AsyncClient,
        thread_url: str,
        cursors: dict[str, str],
        sem: asyncio.Semaphore,
    ) -> tuple[list[DiscussionPost], tuple[str, str] | None]:
        async with sem:
            thread_id = self._thread_id_from_url(thread_url)
            if thread_id is None:
                return [], None
            try:
                html = await self._get(client, thread_url)
            except Exception:
                log.warning("f319 thread page-1 fetch failed: %s", thread_url)
                return [], None
            soup = BeautifulSoup(html, "html.parser")
            total_pages = self._total_pages(soup)
            cursor_post_id = int(cursors.get(thread_id, "0") or "0")

            all_posts: list[DiscussionPost] = []
            page1_posts = self._parse_posts(soup, thread_id, thread_url)
            kept, page_stop = self._filter_by_cursor(page1_posts, cursor_post_id)
            all_posts.extend(kept)

            if total_pages > 1 and not page_stop:
                for p in range(2, total_pages + 1):
                    page_url = f"{thread_url.rstrip('/')}/page-{p}"
                    try:
                        page_html = await self._get(client, page_url)
                    except Exception:
                        log.warning("f319 thread page fetch failed: %s", page_url)
                        break
                    page_soup = BeautifulSoup(page_html, "html.parser")
                    page_posts = self._parse_posts(page_soup, thread_id, page_url)
                    if not page_posts:
                        break
                    kept, page_stop = self._filter_by_cursor(page_posts, cursor_post_id)
                    all_posts.extend(kept)
                    if page_stop:
                        break

            max_post_id = max(
                (int(p.external_id.split("#", 1)[1]) for p in all_posts),
                default=cursor_post_id,
            )
            new_cursor = None
            if max_post_id > cursor_post_id:
                new_cursor = (thread_id, str(max_post_id))
            return all_posts, new_cursor

    @staticmethod
    def _filter_by_cursor(
        posts: list[DiscussionPost], cursor_post_id: int
    ) -> tuple[list[DiscussionPost], bool]:
        kept: list[DiscussionPost] = []
        max_on_page = 0
        for p in posts:
            try:
                pid = int(p.external_id.split("#", 1)[1])
            except (ValueError, IndexError):
                continue
            if pid > max_on_page:
                max_on_page = pid
            if pid > cursor_post_id:
                kept.append(p)
        page_stop = cursor_post_id > 0 and max_on_page <= cursor_post_id
        return kept, page_stop

    @staticmethod
    def _parse_thread_urls(html: str) -> list[str]:
        soup = BeautifulSoup(html, "html.parser")
        urls: list[str] = []
        for li in soup.select("li.discussionListItem"):
            a = li.select_one("a.PreviewTooltip[href^='threads/']")
            if a and a.get("href"):
                urls.append(urljoin(_BASE, a["href"]))
        return urls

    @staticmethod
    def _thread_id_from_url(url: str) -> str | None:
        m = re.search(r"/threads/[^/]+\.(\d+)/", url)
        return m.group(1) if m else None

    @staticmethod
    def _total_pages(soup: BeautifulSoup) -> int:
        nav = soup.select_one("nav.PageNav, div.PageNav")
        if not nav:
            return 1
        last = nav.get("data-last")
        if last and str(last).isdigit():
            return int(last)
        page_nums: list[int] = []
        for a in nav.select("a"):
            txt = a.get_text(strip=True)
            if txt.isdigit():
                page_nums.append(int(txt))
        return max(page_nums) if page_nums else 1

    @staticmethod
    def _parse_posts(
        soup: BeautifulSoup, thread_id: str, page_url: str
    ) -> list[DiscussionPost]:
        title_el = soup.select_one("div.titleBar h1")
        thread_title = title_el.get_text(strip=True) if title_el else None

        out: list[DiscussionPost] = []
        for li in soup.select("li.message[id^='post-']"):
            post_id = li.get("id", "").removeprefix("post-")
            if not post_id:
                continue
            author = li.get("data-author") or None
            dt_el = li.select_one("span.DateTime")
            posted_at = _parse_dt(dt_el.get("title", "") if dt_el else "")
            if posted_at is None:
                continue
            body_el = li.select_one("blockquote.messageText")
            body = body_el.get_text(separator=" ", strip=True) if body_el else ""
            if not body:
                continue
            external_id = f"{thread_id}#{post_id}"
            url = f"{page_url}#post-{post_id}"
            tickers = extract_tickers(f"{thread_title or ''} {body}")
            out.append(
                DiscussionPost(
                    source="f319",
                    external_id=external_id,
                    url=url,
                    posted_at=posted_at,
                    author=author,
                    title=thread_title,
                    body=body,
                    ticker_symbols=tickers,
                )
            )
        return out
