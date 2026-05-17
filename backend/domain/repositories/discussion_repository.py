from abc import ABC, abstractmethod
from datetime import datetime

from domain.entities.discussion_post import DiscussionPost


class DiscussionRepository(ABC):
    @abstractmethod
    async def save_posts(self, posts: list[DiscussionPost]) -> int:
        """Batch upsert posts. Returns count of newly inserted rows."""
        pass

    @abstractmethod
    async def search_by_ticker(
        self, symbol: str, limit: int, since: datetime
    ) -> list[DiscussionPost]:
        pass

    @abstractmethod
    async def search_by_keyword(
        self, keyword: str, limit: int, since: datetime
    ) -> list[DiscussionPost]:
        pass

    @abstractmethod
    async def get_cursor(self, source: str, scope_key: str = "") -> str | None:
        pass

    @abstractmethod
    async def set_cursor(
        self, source: str, external_id: str, scope_key: str = ""
    ) -> None:
        pass

    @abstractmethod
    async def get_cursors(self, source: str) -> dict[str, str]:
        """Return {scope_key: last_external_id} for all scopes under source."""
        pass

    @abstractmethod
    async def log_start(self, source: str | None) -> int:
        pass

    @abstractmethod
    async def log_success(self, log_id: int, inserted: int) -> None:
        pass

    @abstractmethod
    async def log_failure(self, log_id: int, error: str) -> None:
        pass

    @abstractmethod
    async def get_status(self) -> dict:
        pass
