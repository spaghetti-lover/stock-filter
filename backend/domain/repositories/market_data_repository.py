from abc import ABC, abstractmethod


class MarketDataRepository(ABC):
    """Read-side port for market data needed by Layer 2 scoring.

    Methods are sync because the underlying vnstock client is sync. Callers
    that need concurrency should run them in a thread pool.
    """

    @abstractmethod
    def get_trading_history(self, symbol: str, days: int) -> list[dict]:
        """Daily OHLCV rows for ``symbol``, newest-last."""

    @abstractmethod
    def get_intraday(self, symbol: str) -> list[dict]:
        """Today's intraday ticks for ``symbol``."""

    @abstractmethod
    def get_vnindex_history(self, days: int) -> list[dict]:
        """Daily VN-Index OHLCV rows, newest-last."""

    @abstractmethod
    def get_market_flow(self, exchange: str) -> dict[str, dict]:
        """Per-symbol smart-money flow snapshot for an entire ``exchange``."""
