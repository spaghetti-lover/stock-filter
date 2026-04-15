from datetime import datetime, timezone

from db.connection import get_pool
from domain.entities.stock import Stock
from domain.repositories.crawl_repository import CrawlRepository
from infrastructure.persistence.stock_metrics import fetch_all_stocks_live, save_stocks_to_db
from logger import get_logger

log = get_logger(__name__)


class CrawlRepositoryImpl(CrawlRepository):
    async def crawl_all_stocks(self) -> list[Stock]:
        stocks, _ = await fetch_all_stocks_live(expected_fraction=1.0)
        log.info("Crawl complete: %d stocks computed", len(stocks))
        return stocks

    async def save_stocks(self, stocks: list[Stock]) -> None:
        await save_stocks_to_db(stocks)

    async def log_crawl_start(self) -> int:
        pool = get_pool()
        row = await pool.fetchrow(
            "INSERT INTO crawl_log (started_at, status) VALUES ($1, 'running') RETURNING id",
            datetime.now(tz=timezone.utc),
        )
        return row["id"]

    async def log_crawl_success(self, crawl_id: int, total: int, success: int) -> None:
        pool = get_pool()
        await pool.execute(
            "UPDATE crawl_log SET finished_at = $1, status = 'success', total_symbols = $2, success_count = $3 WHERE id = $4",
            datetime.now(tz=timezone.utc), total, success, crawl_id,
        )

    async def log_crawl_failure(self, crawl_id: int, error: str) -> None:
        pool = get_pool()
        await pool.execute(
            "UPDATE crawl_log SET finished_at = $1, status = 'failed', error_message = $2 WHERE id = $3",
            datetime.now(tz=timezone.utc), error, crawl_id,
        )

    async def get_last_crawl_status(self) -> dict | None:
        pool = get_pool()
        row = await pool.fetchrow("SELECT * FROM crawl_log ORDER BY id DESC LIMIT 1")
        return dict(row) if row else None
