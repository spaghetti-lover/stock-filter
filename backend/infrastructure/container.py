from application.services.crawl_service import CrawlUseCase
from application.use_case.get_stock import GetStockUseCase
from application.use_case.layer2_use_case import Layer2UseCase
from infrastructure.persistence.crawl_repository_impl import CrawlRepositoryImpl
from infrastructure.persistence.layer1_repository_impl import Layer1ResultRepositoryImpl
from infrastructure.persistence.layer2_repository_impl import Layer2ScoreRepositoryImpl
from infrastructure.persistence.stock_repository_db import StockRepositoryDB
from infrastructure.persistence.stock_repository_impl import StockRepositoryImpl
from infrastructure.persistence.stock_metrics import save_stocks_to_db
from infrastructure.market_data.data import get_trading_history, get_intraday, get_vnindex_history

_layer1_repo = Layer1ResultRepositoryImpl()
_layer2_repo = Layer2ScoreRepositoryImpl()


def get_layer1_repo() -> Layer1ResultRepositoryImpl:
    return _layer1_repo


def get_live_stock_usecase() -> GetStockUseCase:
    return GetStockUseCase(StockRepositoryImpl(), layer1_repo=_layer1_repo)


def get_cached_stock_usecase() -> GetStockUseCase:
    return GetStockUseCase(
        repo=StockRepositoryDB(),
        fallback_repo=StockRepositoryImpl(),
        save_stocks_fn=save_stocks_to_db,
        layer1_repo=_layer1_repo,
    )


_crawl_usecase: CrawlUseCase | None = None


def get_crawl_usecase() -> CrawlUseCase:
    global _crawl_usecase
    if _crawl_usecase is None:
        _crawl_usecase = CrawlUseCase(CrawlRepositoryImpl(), layer1_repo=_layer1_repo)
    return _crawl_usecase


def get_layer2_usecase() -> Layer2UseCase:
    return Layer2UseCase(
        layer1_repo=_layer1_repo,
        layer2_repo=_layer2_repo,
        get_trading_history_fn=get_trading_history,
        get_intraday_fn=get_intraday,
        get_vnindex_history_fn=get_vnindex_history,
    )
