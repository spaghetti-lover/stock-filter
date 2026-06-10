from abc import ABC, abstractmethod
from enum import Enum
from typing import Awaitable, Callable

from domain.entities.stock import Stock
from domain.value_objects.market_regime import MarketRegime

ProgressCallback = Callable[[int, int, str], Awaitable[None]]


class EarlyRejectKind(str, Enum):
    """Reasons a symbol can be dropped before per-stock filtering runs.
    The user-facing message is composed by the application layer so the
    Layer 1 filter rules remain the single source of truth for wording."""
    NO_HISTORY = "no_history"
    BELOW_MIN_GTGD = "below_min_gtgd"
    FETCH_FAILED = "fetch_failed"


# (symbol, exchange, kind, observed_gtgd_vnd_or_none)
EarlyRejected = tuple[str, str, EarlyRejectKind, float | None]


class Layer1StockRepository(ABC):
    @abstractmethod
    async def list_stocks(
        self,
        exchanges: set[str] | None = None,
        min_gtgd: float = 0.0,
        min_history_sessions: int = 0,
        on_progress: ProgressCallback | None = None,
    ) -> tuple[list[Stock], list[EarlyRejected]]:
        pass

    @abstractmethod
    async def get_market_regime(self) -> MarketRegime | None:
        pass
