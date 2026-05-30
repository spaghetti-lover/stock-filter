from application.dto.smart_money_flow_dto import SmartMoneyFlowResponse
from application.mappers.smart_money_flow_mapper import SmartMoneyFlowMapper
from domain.repositories.smart_money_flow_repository import SmartMoneyFlowRepository


class SmartMoneyFlowUseCase:
    def __init__(self, repo: SmartMoneyFlowRepository):
        self.repo = repo

    async def get_flow(self, symbol: str, days: int) -> SmartMoneyFlowResponse:
        series = await self.repo.get_flow(symbol, days)
        return SmartMoneyFlowMapper.to_response(series)
