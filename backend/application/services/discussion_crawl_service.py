from domain.repositories.discussion_repository import DiscussionRepository
from infrastructure.scrapers.base import DiscussionScraper
from infrastructure.scrapers.ticker_extractor import load_whitelist
from logger import get_logger

log = get_logger(__name__)


class DiscussionCrawlUseCase:
    def __init__(
        self, repo: DiscussionRepository, scrapers: list[DiscussionScraper]
    ):
        self.repo = repo
        self.scrapers = scrapers

    async def execute(self) -> None:
        await load_whitelist()
        for scraper in self.scrapers:
            log_id = await self.repo.log_start(scraper.source)
            try:
                log.info("Discussion scraper '%s' starting", scraper.source)
                inserted = await scraper.run(self.repo)
                await self.repo.log_success(log_id, inserted)
                log.info(
                    "Discussion scraper '%s' done: %d inserted",
                    scraper.source, inserted,
                )
            except Exception as e:
                log.exception("Discussion scraper '%s' failed", scraper.source)
                await self.repo.log_failure(log_id, str(e))

    async def get_status(self) -> dict:
        return await self.repo.get_status()
