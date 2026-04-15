from domain.repositories.crawl_repository import CrawlRepository
from domain.repositories.layer1_repository import Layer1ResultRepository
from application.mappers.stock_mapper import StockMapper
from application.services.stock_filter import apply_filters
from logger import get_logger

log = get_logger(__name__)


class CrawlUseCase:
    def __init__(
        self,
        repo: CrawlRepository,
        layer1_repo: Layer1ResultRepository | None = None,
    ):
        self.repo = repo
        self.layer1_repo = layer1_repo

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

            # Persist Layer 1 results with default filter params
            if self.layer1_repo is not None:
                try:
                    responses = StockMapper.to_response_list(stocks)
                    passed, rejected = apply_filters(responses)
                    await self.layer1_repo.save_results(
                        [s.model_dump() for s in passed],
                        [s.model_dump() for s in rejected],
                    )
                    log.info("Post-crawl layer1: %d passed, %d rejected", len(passed), len(rejected))
                except Exception:
                    log.warning("Failed to persist layer1 results after crawl", exc_info=True)

        except Exception as e:
            log.error("Crawl failed", exc_info=True)
            await self.repo.log_crawl_failure(crawl_id, str(e))

    async def get_status(self) -> dict:
        result = await self.repo.get_last_crawl_status()
        return result if result else {"status": "never run"}
