from abc import ABC, abstractmethod

from domain.entities.layer2_score import Layer2Score


class Layer2ScoreRepository(ABC):
    @abstractmethod
    async def get_cached_scores(self) -> tuple[list[Layer2Score], str | None]:
        """Return cached scores and scored_at timestamp, or ([], None)."""
        pass

    @abstractmethod
    async def get_passed_symbols(self) -> list[dict]:
        """Return [{symbol, exchange}] for stocks that passed Layer 1."""
        pass

    @abstractmethod
    async def save_scores(self, scores: list[Layer2Score]) -> None:
        """Truncate and save scores to layer2_scores."""
        pass
