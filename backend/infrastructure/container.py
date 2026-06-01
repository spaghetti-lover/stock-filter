from application.services.crawl_service import CrawlUseCase
from application.services.discussion_crawl_service import DiscussionCrawlUseCase
from application.use_case.ai_filter_use_case import AIFilterUseCase
from application.use_case.layer1_use_case import Layer1UseCase
from application.use_case.layer2_use_case import Layer2UseCase
from application.use_case.smart_money_flow_use_case import SmartMoneyFlowUseCase
from infrastructure.persistence.crawl_repository_impl import CrawlRepositoryImpl
from infrastructure.persistence.discussion_repository_impl import DiscussionRepositoryImpl
from infrastructure.persistence.layer1_stock_repository_db import Layer1StockRepositoryDB
from infrastructure.persistence.layer1_stock_repository_impl import Layer1StockRepositoryImpl
from infrastructure.persistence.layer2_score_repository_db import Layer2ScoreRepositoryDB
from infrastructure.persistence.smart_money_flow_repository_impl import SmartMoneyFlowRepositoryImpl
from infrastructure.persistence.stock_metrics import save_stocks_to_db
from infrastructure.scrapers.f247 import F247Scraper
from infrastructure.scrapers.f319 import F319Scraper


def get_live_layer1_usecase(save: bool = False) -> Layer1UseCase:
    return Layer1UseCase(
        Layer1StockRepositoryImpl(),
        save_stocks_fn=save_stocks_to_db if save else None,
    )


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


def get_layer2_usecase() -> Layer2UseCase:
    return Layer2UseCase(repo=Layer2ScoreRepositoryDB())


def get_smart_money_flow_usecase() -> SmartMoneyFlowUseCase:
    return SmartMoneyFlowUseCase(repo=SmartMoneyFlowRepositoryImpl())


_discussion_usecase: DiscussionCrawlUseCase | None = None


def get_discussion_crawl_usecase() -> DiscussionCrawlUseCase:
    global _discussion_usecase
    if _discussion_usecase is None:
        repo = DiscussionRepositoryImpl()
        scrapers = [F319Scraper(), F247Scraper()]
        _discussion_usecase = DiscussionCrawlUseCase(repo, scrapers)
    return _discussion_usecase


def get_ai_filter_usecase(provider: str = "claude") -> AIFilterUseCase:
    from infrastructure.agents.factory import get_agent_provider
    from infrastructure.tools import ToolSet

    agent = get_agent_provider(provider, toolset=ToolSet(names=()))
    return AIFilterUseCase(provider=agent, repo=Layer1StockRepositoryDB())
