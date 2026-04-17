import asyncio
from datetime import datetime, timezone, timedelta

from domain.entities.stock import Stock
from domain.repositories.layer1_stock_repository import EarlyRejected, ProgressCallback, Layer1StockRepository
from domain.value_objects.market_regime import MarketRegime
from infrastructure.market_data.data import get_vnindex_history
from infrastructure.persistence.stock_metrics import (
    executor, get_expected_fraction_at_time,
    compute_market_regime, fetch_all_stocks_live,
)
from logger import get_logger

log = get_logger(__name__)


class Layer1StockRepositoryImpl(Layer1StockRepository):
    async def list_stocks(
        self,
        exchanges: set[str] | None = None,
        min_gtgd: float = 0.0,
        min_history_sessions: int = 0,
        on_progress: ProgressCallback | None = None,
    ) -> tuple[list[Stock], list[EarlyRejected]]:
        now = datetime.now(tz=timezone(timedelta(hours=7)))
        expected_fraction = get_expected_fraction_at_time(now.hour, now.minute)
        log.info("list_stocks started: exchanges=%s min_gtgd=%s fraction=%.2f", exchanges, min_gtgd, expected_fraction)
        return await fetch_all_stocks_live(
            exchanges, min_gtgd, min_history_sessions, expected_fraction, on_progress,
        )

    async def get_market_regime(self) -> MarketRegime | None:
        loop = asyncio.get_event_loop()
        rows = await loop.run_in_executor(executor, get_vnindex_history, 40)
        regime = compute_market_regime(rows)
        if regime:
            log.info("Market regime: %s (close=%.2f ma5=%.2f ma20=%.2f ratio=%.4f)", regime.state, regime.vnindex_close, regime.vnindex_ma5, regime.vnindex_ma20, regime.ratio)
        else:
            log.warning("VNINDEX history insufficient, skipping regime gate")
        return regime
