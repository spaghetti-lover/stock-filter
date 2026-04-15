from abc import ABC, abstractmethod


class Layer1ResultRepository(ABC):
    @abstractmethod
    async def save_results(
        self,
        passed: list[dict],
        rejected: list[dict],
    ) -> None:
        """Persist Layer 1 filter results (TRUNCATE + insert)."""
        pass

    @abstractmethod
    async def get_passed_symbols(self) -> list[dict]:
        """Return all rows where result='passed'."""
        pass

    @abstractmethod
    async def has_results(self) -> bool:
        """Return True if layer1_results has any rows."""
        pass
