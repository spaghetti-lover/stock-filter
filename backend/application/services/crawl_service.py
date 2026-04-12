from domain.repositories.crawl_repository import CrawlRepository
from logger import get_logger

log = get_logger(__name__)


class CrawlUseCase:
    def __init__(self, repo: CrawlRepository):
        self.repo = repo

    async def execute(self):
        crawl_id = await self.repo.log_crawl_start()
        log.info("Crawl started (id=%d)", crawl_id)

        try:
            stocks = await self.repo.crawl_all_stocks()
            total = len(stocks)
            log.info("Crawl: computed %d stocks, saving to DB", total)

            await self.repo.save_stocks(stocks)
            await self.repo.log_crawl_success(crawl_id, total, total)
            log.info("Crawl finished: %d stocks stored", total)

        except Exception as e:
            log.error("Crawl failed", exc_info=True)
            await self.repo.log_crawl_failure(crawl_id, str(e))

    async def get_status(self) -> dict:
        result = await self.repo.get_last_crawl_status()
        return result if result else {"status": "never run"}
