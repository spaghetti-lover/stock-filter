from domain.repositories.market_data_repository import MarketDataRepository
from infrastructure.market_data.data import (
    get_intraday,
    get_market_flow,
    get_trading_history,
    get_vnindex_history,
)


class MarketDataRepositoryImpl(MarketDataRepository):
    """Adapter over the rate-limited vnstock client in infrastructure.market_data."""

    def get_trading_history(self, symbol: str, days: int) -> list[dict]:
        return get_trading_history(symbol, days)

    def get_intraday(self, symbol: str) -> list[dict]:
        return get_intraday(symbol)

    def get_vnindex_history(self, days: int) -> list[dict]:
        return get_vnindex_history(days)

    def get_market_flow(self, exchange: str) -> dict[str, dict]:
        return get_market_flow(exchange)
