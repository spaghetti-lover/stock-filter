import asyncio
from concurrent.futures import ThreadPoolExecutor

from db.connection import get_pool
from domain.entities.stock import Stock
from domain.repositories.stock_repository import EarlyRejected, ProgressCallback, StockRepository
from domain.value_objects.market_regime import MarketRegime
from infrastructure.market_data.data import get_vnindex_history

_executor = ThreadPoolExecutor(max_workers=5)


class StockRepositoryDB(StockRepository):
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
        rows = await loop.run_in_executor(_executor, get_vnindex_history, 40)
        if not rows or len(rows) < 20:
            return None
        closes = [r["close"] for r in rows]
        vnindex_close = closes[-1]
        ma5 = sum(closes[-5:]) / 5
        ma20 = sum(closes[-20:]) / 20
        return MarketRegime.from_values(close=vnindex_close, ma5=ma5, ma20=ma20)
