import asyncio

from db.connection import get_pool
from domain.entities.stock import Stock
from domain.repositories.layer1_stock_repository import EarlyRejected, ProgressCallback, Layer1StockRepository
from domain.value_objects.market_regime import MarketRegime
from infrastructure.market_data.data import get_vnindex_history
from infrastructure.persistence.stock_metrics import executor, compute_market_regime


class Layer1StockRepositoryDB(Layer1StockRepository):
    async def list_stocks(
        self,
        exchanges: set[str] | None = None,
        min_gtgd: float = 0.0,
        min_history_sessions: int = 0,
        on_progress: ProgressCallback | None = None,
    ) -> tuple[list[Stock], list[EarlyRejected]]:
        pool = get_pool()

        query = "SELECT * FROM stock_metrics"
        conditions = []
        args = []
        idx = 1

        if exchanges:
            placeholders = ", ".join(f"${idx + i}" for i in range(len(exchanges)))
            conditions.append(f"exchange IN ({placeholders})")
            args.extend(exchanges)
            idx += len(exchanges)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        rows = await pool.fetch(query, *args)
        stocks = [
            Stock(
                symbol=row["symbol"],
                exchange=row["exchange"],
                status=row["status"],
                price=row["price"],
                gtgd20=row["gtgd20"],
                history_sessions=row["history_sessions"],
                today_value=row["today_value"],
                avg_intraday_expected=row["avg_intraday_expected"],
                intraday_ratio=row["intraday_ratio"],
                is_ceiling=row["is_ceiling"],
                is_floor=row["is_floor"],
                cv=row["cv"],
            )
            for row in rows
        ]
        return stocks, []

    async def get_market_regime(self) -> MarketRegime | None:
        loop = asyncio.get_event_loop()
        rows = await loop.run_in_executor(executor, get_vnindex_history, 40)
        return compute_market_regime(rows)
