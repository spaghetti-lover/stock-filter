from dataclasses import dataclass
from typing import List

from app.domain.entities.stock import Stock
from app.domain.services.stock_filter_service import StockFilterService


@dataclass
class ScreenerRequest:
    min_price: float = 5.0
    max_price: float = 10_000.0
    min_avg_volume: float = 100_000
    min_range_pct: float = 0.5
    lookback_days: int = 20


@dataclass
class ScreenerResponse:
    stocks: List[Stock]
    total: int


class RunStockScreener:
    def __init__(self, service: StockFilterService):
        self._service = service

    def execute(self, req: ScreenerRequest) -> ScreenerResponse:
        stocks = self._service.filter(
            min_price=req.min_price,
            max_price=req.max_price,
            min_avg_volume=req.min_avg_volume,
            min_range_pct=req.min_range_pct,
            lookback_days=req.lookback_days,
        )
        return ScreenerResponse(stocks=stocks, total=len(stocks))
