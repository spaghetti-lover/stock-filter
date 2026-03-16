from abc import ABC, abstractmethod
from typing import List
from app.domain.entities.stock import Stock
from app.domain.entities.ohlcv import OHLCV


class MarketDataRepository(ABC):
    @abstractmethod
    def get_all_stocks(self) -> List[Stock]:
        ...

    @abstractmethod
    def get_ohlcv(self, symbol: str, days: int = 20) -> List[OHLCV]:
        ...
