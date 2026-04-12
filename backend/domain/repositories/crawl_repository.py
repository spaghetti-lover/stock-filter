from abc import ABC, abstractmethod

from domain.entities.stock import Stock


class CrawlRepository(ABC):
    @abstractmethod
    async def crawl_all_stocks(self) -> list[Stock]:
        """Fetch all symbols from market data source and compute metrics."""
        pass

    @abstractmethod
    async def save_stocks(self, stocks: list[Stock]) -> None:
        """Persist computed stock metrics (full replace)."""
        pass

    @abstractmethod
    async def log_crawl_start(self) -> int:
        """Record crawl start, return crawl ID."""
        pass

    @abstractmethod
    async def log_crawl_success(self, crawl_id: int, total: int, success: int) -> None:
        pass

    @abstractmethod
    async def log_crawl_failure(self, crawl_id: int, error: str) -> None:
        pass

    @abstractmethod
    async def get_last_crawl_status(self) -> dict | None:
        pass
