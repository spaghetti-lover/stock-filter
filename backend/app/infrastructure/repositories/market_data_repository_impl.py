import random
from datetime import date, timedelta
from typing import List

from app.domain.entities.ohlcv import OHLCV
from app.domain.entities.stock import Stock
from app.domain.repositories.market_data_repository import MarketDataRepository

# Fake in-memory data for testing — replace with real API calls later
_STOCKS = [
    Stock("VNM", "Vinamilk", "HOSE", "Consumer Staples"),
    Stock("VIC", "Vingroup", "HOSE", "Real Estate"),
    Stock("HPG", "Hoa Phat Group", "HOSE", "Materials"),
    Stock("FPT", "FPT Corporation", "HOSE", "Technology"),
    Stock("MBB", "MB Bank", "HOSE", "Financials"),
]


class InMemoryMarketDataRepository(MarketDataRepository):
    def get_all_stocks(self) -> List[Stock]:
        return list(_STOCKS)

    def get_ohlcv(self, symbol: str, days: int = 20) -> List[OHLCV]:
        random.seed(symbol)
        result = []
        base_price = random.uniform(20, 200)
        today = date.today()
        for i in range(days):
            d = today - timedelta(days=days - i)
            open_ = base_price * random.uniform(0.98, 1.02)
            close = open_ * random.uniform(0.97, 1.03)
            high = max(open_, close) * random.uniform(1.0, 1.02)
            low = min(open_, close) * random.uniform(0.98, 1.0)
            volume = random.uniform(50_000, 500_000)
            result.append(OHLCV(symbol, d, open_, high, low, close, volume))
            base_price = close
        return result
