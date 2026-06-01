import asyncio
from datetime import datetime
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

_BASE = "https://f247.com"
_CATEGORY_PATH = "/c/chung-khoan/5"
_TOPIC_CONCURRENCY = 5
_REQUEST_DELAY_SEC = 0.3
_BATCH_SIZE = 200
_POST_IDS_CHUNK = 20


class _Retry(Exception):
    pass


def _parse_iso(s: str) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


class F247Scraper(DiscussionScraper):
    source = "f247"

    def __init__(self, topic_concurrency: int = _TOPIC_CONCURRENCY) -> None:
        self.topic_concurrency = topic_concurrency

    @retry(
        retry=retry_if_exception_type(_Retry),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=20),
        reraise=True,
    )
    async def _get_json(
        self,
        client: httpx.AsyncClient,
        url: str,
        params: list[tuple[str, str]] | None = None,
    ) -> dict:
        resp = await client.get(url, params=params)
        if resp.status_code == 403:
            log.warning("f247 %s -> 403 Forbidden, not retrying", url)
            resp.raise_for_status()
        if resp.status_code in (429, 503):
            log.warning("f247 %s -> %d, will retry", url, resp.status_code)
            raise _Retry(f"{resp.status_code}")
        resp.raise_for_status()
        await asyncio.sleep(_REQUEST_DELAY_SEC)
        return resp.json()

    async def run(self, repo) -> int:
        cursors = await repo.get_cursors(self.source)
        log.info("f247 starting backfill: %d known topic cursors", len(cursors))

        total_inserted = 0
        async with build_http_client() as client:
            page = 0
            while True:
                page += 1
                url = urljoin(_BASE, f"{_CATEGORY_PATH}.json")
                try:
                    listing = await self._get_json(
                        client, url, params=[("page", str(page - 1))]
                    )
                except Exception:
                    log.exception("f247 listing page %d failed, stopping", page)
                    break

                topic_list = listing.get("topic_list") or {}
                topics = topic_list.get("topics") or []
                if not topics:
                    log.info("f247 listing page %d empty, end of category", page)
                    break

                fresh = [
                    t for t in topics
                    if int(t.get("highest_post_number") or 0)
                    > int(cursors.get(str(t["id"]), "0") or "0")
                ]
                log.info(
                    "f247 listing page %d: %d topics (%d fresh)",
                    page, len(topics), len(fresh),
                )

                if fresh:
                    sem = asyncio.Semaphore(self.topic_concurrency)
                    results = await asyncio.gather(
                        *(
                            self._crawl_topic(client, t, cursors, sem)
                            for t in fresh
                        ),
                        return_exceptions=True,
                    )

                    batch_posts: list[DiscussionPost] = []
                    cursor_updates: list[tuple[str, str]] = []
                    seen_ext: set[str] = set()
                    for r in results:
                        if isinstance(r, BaseException):
                            log.warning("f247 topic error: %s", r)
                            continue
                        posts, new_cursor = r
                        if new_cursor is not None:
                            cursor_updates.append(new_cursor)
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

                    for topic_id, max_pn in cursor_updates:
                        cursors[topic_id] = max_pn
                        await repo.set_cursor(self.source, max_pn, topic_id)

                log.info(
                    "f247 page %d done: %d inserts cumulative",
                    page, total_inserted,
                )

                more = topic_list.get("more_topics_url")
                if not more:
                    log.info("f247 no more pages, stopping")
                    break

                if not fresh and all(
                    str(t["id"]) in cursors for t in topics
                ):
                    log.info(
                        "f247 page %d had no fresh topics and all known; stopping early",
                        page,
                    )
                    break

        log.info("f247 backfill finished: %d posts inserted", total_inserted)
        return total_inserted

    async def _crawl_topic(
        self,
        client: httpx.AsyncClient,
        topic_summary: dict,
        cursors: dict[str, str],
        sem: asyncio.Semaphore,
    ) -> tuple[list[DiscussionPost], tuple[str, str] | None]:
        async with sem:
            topic_id = topic_summary["id"]
            slug = topic_summary.get("slug") or ""
            cursor_pn = int(cursors.get(str(topic_id), "0") or "0")

            url = urljoin(_BASE, f"/t/{slug}/{topic_id}.json")
            try:
                topic_json = await self._get_json(client, url)
            except Exception:
                log.warning("f247 topic fetch failed: %s", url)
                return [], None

            title = (
                topic_json.get("fancy_title")
                or topic_json.get("title")
                or ""
            )
            tags = topic_json.get("tags") or []
            post_stream = topic_json.get("post_stream") or {}
            stream = post_stream.get("stream") or []
            first_posts = post_stream.get("posts") or []

            loaded: dict[int, dict] = {p["id"]: p for p in first_posts if "id" in p}

            needed_ids = [
                stream[i] for i in range(len(stream))
                if (i + 1) > cursor_pn
            ]

            missing = [pid for pid in needed_ids if pid not in loaded]
            for i in range(0, len(missing), _POST_IDS_CHUNK):
                chunk = missing[i:i + _POST_IDS_CHUNK]
                try:
                    extra = await self._fetch_post_chunk(client, topic_id, chunk)
                except Exception:
                    log.warning(
                        "f247 posts.json chunk failed for topic %s",
                        topic_id,
                    )
                    break
                for p in extra:
                    if "id" in p:
                        loaded[p["id"]] = p

            out: list[DiscussionPost] = []
            max_pn_seen = cursor_pn
            for pid in needed_ids:
                raw = loaded.get(pid)
                if raw is None:
                    continue
                dp = self._to_discussion_post(raw, topic_id, slug, title, tags)
                if dp is None:
                    continue
                out.append(dp)
                pn = int(raw.get("post_number") or 0)
                if pn > max_pn_seen:
                    max_pn_seen = pn

            new_cursor = (
                (str(topic_id), str(max_pn_seen))
                if max_pn_seen > cursor_pn
                else None
            )
            return out, new_cursor

    async def _fetch_post_chunk(
        self,
        client: httpx.AsyncClient,
        topic_id: int,
        post_ids: list[int],
    ) -> list[dict]:
        params = [("post_ids[]", str(pid)) for pid in post_ids]
        url = urljoin(_BASE, f"/t/{topic_id}/posts.json")
        data = await self._get_json(client, url, params=params)
        return (data.get("post_stream") or {}).get("posts") or []

    @staticmethod
    def _to_discussion_post(
        raw: dict,
        topic_id: int,
        slug: str,
        topic_title: str,
        topic_tags: list[str],
    ) -> DiscussionPost | None:
        cooked = raw.get("cooked") or ""
        body = BeautifulSoup(cooked, "html.parser").get_text(
            separator=" ", strip=True
        )
        if not body:
            return None

        post_id = raw.get("id")
        post_number = raw.get("post_number")
        if post_id is None or post_number is None:
            return None

        posted_at = _parse_iso(raw.get("created_at", ""))
        if posted_at is None:
            return None

        external_id = f"{topic_id}#{post_id}"
        url = f"{_BASE}/t/{slug}/{topic_id}/{post_number}"
        author = raw.get("username") or None
        tickers = extract_tickers(
            f"{topic_title} {body} {' '.join(topic_tags)}"
        )

        return DiscussionPost(
            source="f247",
            external_id=external_id,
            url=url,
            posted_at=posted_at,
            author=author,
            title=topic_title or None,
            body=body,
            ticker_symbols=tickers,
        )
