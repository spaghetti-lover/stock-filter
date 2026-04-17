from application.services.crawl_service import CrawlUseCase
from application.use_case.layer1_use_case import Layer1UseCase
from infrastructure.persistence.crawl_repository_impl import CrawlRepositoryImpl
from infrastructure.persistence.layer1_stock_repository_db import Layer1StockRepositoryDB
from infrastructure.persistence.layer1_stock_repository_impl import Layer1StockRepositoryImpl
from infrastructure.persistence.stock_metrics import save_stocks_to_db


def get_live_layer1_usecase() -> Layer1UseCase:
    return Layer1UseCase(Layer1StockRepositoryImpl())


def get_cached_layer1_usecase() -> Layer1UseCase:
    return Layer1UseCase(
        repo=Layer1StockRepositoryDB(),
        fallback_repo=Layer1StockRepositoryImpl(),
        save_stocks_fn=save_stocks_to_db,
    )


_crawl_usecase: CrawlUseCase | None = None


def get_crawl_usecase() -> CrawlUseCase:
    global _crawl_usecase
    if _crawl_usecase is None:
        _crawl_usecase = CrawlUseCase(CrawlRepositoryImpl())
    return _crawl_usecase
