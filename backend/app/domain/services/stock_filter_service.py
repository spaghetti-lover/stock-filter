from typing import List
from app.domain.entities.stock import Stock
from app.domain.repositories.market_data_repository import MarketDataRepository
from app.domain.rules.liquidity_rule import passes_liquidity_rule
from app.domain.rules.price_rule import passes_price_rule
from app.domain.rules.intraday_activity_rule import passes_intraday_activity_rule
from app.domain.rules.data_quality_rule import passes_data_quality_rule


class StockFilterService:
    def __init__(self, repo: MarketDataRepository):
        self._repo = repo

    def filter(
        self,
        min_price: float = 5.0,
        max_price: float = 10_000.0,
        min_avg_volume: float = 100_000,
        min_range_pct: float = 0.5,
        lookback_days: int = 20,
    ) -> List[Stock]:
        stocks = self._repo.get_all_stocks()
        result = []
        for stock in stocks:
            ohlcv = self._repo.get_ohlcv(stock.symbol, days=lookback_days)
            if (
                passes_data_quality_rule(ohlcv)
                and passes_price_rule(ohlcv, min_price, max_price)
                and passes_liquidity_rule(ohlcv, min_avg_volume)
                and passes_intraday_activity_rule(ohlcv, min_range_pct)
            ):
                result.append(stock)
        return result
