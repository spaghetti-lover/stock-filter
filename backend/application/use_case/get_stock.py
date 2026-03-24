from domain.repositories.stock_repository import StockRepository
from application.mappers.stock_mapper import StockMapper


class GetStockUseCase:
    def __init__(self, repo: StockRepository):
        self.repo = repo

    async def execute(self, exchanges: set[str] | None = None, min_gtgd: float = 0.0):
        stocks = await self.repo.list_stocks(exchanges=exchanges, min_gtgd=min_gtgd)
        return StockMapper.to_response_list(stocks)
