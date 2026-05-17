from datetime import datetime, timezone

from db.connection import get_pool
from domain.entities.discussion_post import DiscussionPost
from domain.repositories.discussion_repository import DiscussionRepository
from logger import get_logger

log = get_logger(__name__)


def _row_to_post(row) -> DiscussionPost:
    return DiscussionPost(
        source=row["source"],
        external_id=row["external_id"],
        url=row["url"],
        posted_at=row["posted_at"],
        author=row["author"],
        title=row["title"],
        body=row["body"],
        ticker_symbols=tuple(row["ticker_symbols"] or ()),
    )


class DiscussionRepositoryImpl(DiscussionRepository):
    async def save_posts(self, posts: list[DiscussionPost]) -> int:
        if not posts:
            return 0
        pool = get_pool()
        records = [
            (
                p.source,
                p.external_id,
                list(p.ticker_symbols),
                p.author,
                p.posted_at,
                p.title,
                p.body,
                p.url,
            )
            for p in posts
        ]
        async with pool.acquire() as conn:
            async with conn.transaction():
                before = await conn.fetchval(
                    "SELECT COUNT(*) FROM discussion_posts"
                )
                await conn.executemany(
                    """
                    INSERT INTO discussion_posts
                        (source, external_id, ticker_symbols, author, posted_at, title, body, url)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (source, external_id) DO NOTHING
                    """,
                    records,
                )
                after = await conn.fetchval(
                    "SELECT COUNT(*) FROM discussion_posts"
                )
        return int(after - before)

    async def search_by_ticker(
        self, symbol: str, limit: int, since: datetime
    ) -> list[DiscussionPost]:
        pool = get_pool()
        rows = await pool.fetch(
            """
            SELECT source, external_id, url, posted_at, author, title, body, ticker_symbols
            FROM discussion_posts
            WHERE $1 = ANY(ticker_symbols) AND posted_at >= $2
            ORDER BY posted_at DESC
            LIMIT $3
            """,
            symbol.upper(), since, limit,
        )
        return [_row_to_post(r) for r in rows]

    async def search_by_keyword(
        self, keyword: str, limit: int, since: datetime
    ) -> list[DiscussionPost]:
        pool = get_pool()
        rows = await pool.fetch(
            """
            SELECT source, external_id, url, posted_at, author, title, body, ticker_symbols,
                   ts_rank(body_tsv, q) AS rank
            FROM discussion_posts, plainto_tsquery('simple', $1) q
            WHERE body_tsv @@ q AND posted_at >= $2
            ORDER BY rank DESC, posted_at DESC
            LIMIT $3
            """,
            keyword, since, limit,
        )
        return [_row_to_post(r) for r in rows]

    async def get_cursor(self, source: str, scope_key: str = "") -> str | None:
        pool = get_pool()
        row = await pool.fetchrow(
            "SELECT last_external_id FROM scraper_cursor WHERE source = $1 AND scope_key = $2",
            source, scope_key,
        )
        return row["last_external_id"] if row else None

    async def set_cursor(
        self, source: str, external_id: str, scope_key: str = ""
    ) -> None:
        pool = get_pool()
        await pool.execute(
            """
            INSERT INTO scraper_cursor (source, scope_key, last_external_id, updated_at)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (source, scope_key) DO UPDATE
              SET last_external_id = EXCLUDED.last_external_id,
                  updated_at       = EXCLUDED.updated_at
            """,
            source, scope_key, external_id, datetime.now(tz=timezone.utc),
        )

    async def get_cursors(self, source: str) -> dict[str, str]:
        pool = get_pool()
        rows = await pool.fetch(
            "SELECT scope_key, last_external_id FROM scraper_cursor WHERE source = $1",
            source,
        )
        return {r["scope_key"]: r["last_external_id"] for r in rows if r["last_external_id"]}

    async def log_start(self, source: str | None) -> int:
        pool = get_pool()
        row = await pool.fetchrow(
            """
            INSERT INTO discussion_crawl_log (source, started_at, status)
            VALUES ($1, $2, 'running')
            RETURNING id
            """,
            source, datetime.now(tz=timezone.utc),
        )
        return row["id"]

    async def log_success(self, log_id: int, inserted: int) -> None:
        pool = get_pool()
        await pool.execute(
            """
            UPDATE discussion_crawl_log
            SET finished_at = $1, status = 'success', inserted_count = $2
            WHERE id = $3
            """,
            datetime.now(tz=timezone.utc), inserted, log_id,
        )

    async def log_failure(self, log_id: int, error: str) -> None:
        pool = get_pool()
        await pool.execute(
            """
            UPDATE discussion_crawl_log
            SET finished_at = $1, status = 'failed', error_message = $2
            WHERE id = $3
            """,
            datetime.now(tz=timezone.utc), error, log_id,
        )

    async def get_status(self) -> dict:
        pool = get_pool()
        rows = await pool.fetch(
            """
            SELECT DISTINCT ON (source) *
            FROM discussion_crawl_log
            WHERE source IS NOT NULL
            ORDER BY source, id DESC
            """
        )
        if not rows:
            return {"status": "never run"}
        return {"sources": [dict(r) for r in rows]}
