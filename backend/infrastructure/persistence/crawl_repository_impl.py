import asyncio
from datetime import datetime, timezone

from db.connection import get_pool
from domain.entities.stock import Stock
from domain.repositories.crawl_repository import CrawlRepository
from infrastructure.market_data.data import get_all_symbols, get_trading_history, get_intraday
from infrastructure.persistence.stock_metrics import executor, CONCURRENCY, compute_stock_metrics
from logger import get_logger

log = get_logger(__name__)


class CrawlRepositoryImpl(CrawlRepository):
    async def crawl_all_stocks(self) -> list[Stock]:
        loop = asyncio.get_event_loop()
        symbols = await loop.run_in_executor(executor, get_all_symbols)
        log.info("Crawl: fetching %d symbols", len(symbols))

        expected_fraction = 1.0  # end of day
        sem = asyncio.Semaphore(CONCURRENCY)
        total = len(symbols)
        processed = 0
        failed = 0
        results: list[Stock] = []
        counter_lock = asyncio.Lock()

        async def process(item: dict):
            nonlocal processed, failed
            symbol = item["symbol"]
            exchange = item["exchange"]
            async with sem:
                try:
                    history_fut = loop.run_in_executor(executor, get_trading_history, symbol, 90)
                    intraday_fut = loop.run_in_executor(executor, get_intraday, symbol)
                    history_rows, intraday_rows = await asyncio.gather(history_fut, intraday_fut)

                    stock = compute_stock_metrics(symbol, exchange, history_rows, intraday_rows, expected_fraction)
                    if stock is not None:
                        results.append(stock)
                except Exception:
                    async with counter_lock:
                        failed += 1
                    log.warning("Crawl: failed to process %s", symbol, exc_info=True)

            async with counter_lock:
                processed += 1
                if processed % 50 == 0 or processed == total:
                    log.info("Crawl progress: %d/%d (%.0f%%) — %d failed", processed, total, processed / total * 100, failed)

        await asyncio.gather(*[process(item) for item in symbols])
        log.info("Crawl complete: %d stocks computed, %d failed out of %d", len(results), failed, total)
        return results

    async def save_stocks(self, stocks: list[Stock]) -> None:
        pool = get_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("TRUNCATE stock_metrics")
                now = datetime.now(tz=timezone.utc)
                await conn.executemany(
                    """INSERT INTO stock_metrics
                       (symbol, exchange, status, price, gtgd20, history_sessions,
                        today_value, avg_intraday_expected, intraday_ratio,
                        is_ceiling, is_floor, cv, crawled_at)
                       VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)""",
                    [
                        (
                            s.symbol, s.exchange, s.status, s.price, s.gtgd20,
                            s.history_sessions, s.today_value, s.avg_intraday_expected,
                            s.intraday_ratio, s.is_ceiling, s.is_floor, s.cv, now,
                        )
                        for s in stocks
                    ],
                )

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
