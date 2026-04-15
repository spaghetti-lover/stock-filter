from abc import ABC, abstractmethod


class Layer2ScoreRepository(ABC):
    @abstractmethod
    async def save_scores(self, scores: list[dict]) -> None:
        """Persist Layer 2 BUY scores (TRUNCATE + insert)."""
        pass

    @abstractmethod
    async def get_scores(self) -> list[dict]:
        """Return all rows from layer2_scores."""
        pass

    @abstractmethod
    async def has_scores(self) -> bool:
        """Return True if layer2_scores has any rows."""
        pass
