# domain/repositories/todo_repository.py
from abc import ABC, abstractmethod

from domain.entities.stock import Stock

class StockRepository(ABC):
    @abstractmethod
    def list_stocks(self, exchanges: set[str] | None = None, min_gtgd: float = 0.0) -> list[Stock]:
        pass