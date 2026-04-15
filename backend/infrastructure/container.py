from application.services.crawl_service import CrawlUseCase
from application.use_case.get_stock import GetStockUseCase
from infrastructure.persistence.crawl_repository_impl import CrawlRepositoryImpl
from infrastructure.persistence.stock_repository_db import StockRepositoryDB
from infrastructure.persistence.stock_repository_impl import StockRepositoryImpl
from infrastructure.persistence.stock_metrics import save_stocks_to_db


def get_live_stock_usecase() -> GetStockUseCase:
    return GetStockUseCase(StockRepositoryImpl())


def get_cached_stock_usecase() -> GetStockUseCase:
    return GetStockUseCase(
        repo=StockRepositoryDB(),
        fallback_repo=StockRepositoryImpl(),
        save_stocks_fn=save_stocks_to_db,
    )


_crawl_usecase: CrawlUseCase | None = None


def get_crawl_usecase() -> CrawlUseCase:
    global _crawl_usecase
    if _crawl_usecase is None:
        _crawl_usecase = CrawlUseCase(CrawlRepositoryImpl())
    return _crawl_usecase
