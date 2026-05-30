from abc import ABC, abstractmethod

from domain.entities.smart_money_flow_series import SmartMoneyFlowSeries


class SmartMoneyFlowRepository(ABC):
    @abstractmethod
    async def get_flow(self, symbol: str, days: int) -> SmartMoneyFlowSeries:
        pass
