from fastapi import APIRouter, Query

from app.usecases.run_stock_screener import RunStockScreener, ScreenerRequest
from app.domain.services.stock_filter_service import StockFilterService
from app.infrastructure.repositories.market_data_repository_impl import InMemoryMarketDataRepository

router = APIRouter(prefix="/screener", tags=["screener"])

# Dependency composition (simple — swap repo/service via DI framework if needed)
_repo = InMemoryMarketDataRepository()
_service = StockFilterService(_repo)
_use_case = RunStockScreener(_service)


@router.get("")
def screen_stocks(
    min_price: float = Query(default=5.0, description="Minimum close price"),
    max_price: float = Query(default=10_000.0, description="Maximum close price"),
    min_avg_volume: float = Query(default=100_000, description="Minimum average daily volume"),
    min_range_pct: float = Query(default=0.5, description="Minimum intraday range %"),
    lookback_days: int = Query(default=20, description="Number of historical days to analyse"),
):
    req = ScreenerRequest(
        min_price=min_price,
        max_price=max_price,
        min_avg_volume=min_avg_volume,
        min_range_pct=min_range_pct,
        lookback_days=lookback_days,
    )
    resp = _use_case.execute(req)
    return {
        "total": resp.total,
        "stocks": [
            {
                "symbol": s.symbol,
                "name": s.name,
                "exchange": s.exchange,
                "sector": s.sector,
            }
            for s in resp.stocks
        ],
    }
