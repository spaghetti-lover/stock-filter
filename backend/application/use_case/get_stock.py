from domain.entities.stock import Stock
from domain.repositories.stock_repository import StockRepository
from application.mappers.stock_mapper import StockMapper

class GetStockUseCase:
    def __init__(self, repo: StockRepository):
        self.repo = repo

    def execute(self, exchanges: set[str] | None = None):
        stocks = self.repo.list_stocks(exchanges=exchanges)
        return StockMapper.to_response_list(stocks)