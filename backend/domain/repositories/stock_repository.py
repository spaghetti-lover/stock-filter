from abc import ABC, abstractmethod
from typing import Awaitable, Callable

from domain.entities.stock import Stock

ProgressCallback = Callable[[int, int, str], Awaitable[None]]


class StockRepository(ABC):
    @abstractmethod
    async def list_stocks(
        self,
        exchanges: set[str] | None = None,
        min_gtgd: float = 0.0,
        min_history_sessions: int = 0,
        on_progress: ProgressCallback | None = None,
    ) -> list[Stock]:
        pass
