from datetime import datetime, timezone, timedelta

import asyncpg

from domain.entities.stock import Stock
from domain.repositories.stock_repository import StockRepository
from db.connection import get_pool
from logger import get_logger

log = get_logger(__name__)

INTRADAY_TIME_SLOTS = [
    (9, 0), (9, 30), (10, 0), (10, 30), (11, 0), (11, 30),
    (13, 0), (13, 30), (14, 0), (14, 30), (15, 0)
]
INTRADAY_CUMULATIVE = [0.12, 0.22, 0.30, 0.37, 0.43, 0.48, 0.56, 0.65, 0.75, 0.86, 1.00]


def _get_expected_fraction_at_time(hour: int, minute: int) -> float:
    if (hour, minute) < (9, 0):
        return 0.0
    for i, (h, m) in enumerate(INTRADAY_TIME_SLOTS):
        if (hour, minute) <= (h, m):
            if i == 0:
                return INTRADAY_CUMULATIVE[0]
            prev_h, prev_m = INTRADAY_TIME_SLOTS[i - 1]
            elapsed = (hour * 60 + minute) - (prev_h * 60 + prev_m)
            slot_len = (h * 60 + m) - (prev_h * 60 + prev_m)
            ratio = elapsed / max(slot_len, 1)
            return INTRADAY_CUMULATIVE[i - 1] + (INTRADAY_CUMULATIVE[i] - INTRADAY_CUMULATIVE[i - 1]) * ratio
    return 1.0


_QUERY = """
SELECT
    s.symbol, s.exchange, s.status,
    m.current_price, m.gtgd20, m.history_sessions,
    COALESCE(id.today_value, 0) AS today_value
FROM symbols s
JOIN stock_metrics m ON m.symbol = s.symbol
LEFT JOIN intraday_daily id ON id.symbol = s.symbol AND id.snap_date = CURRENT_DATE
WHERE ($1::text[] IS NULL OR s.exchange = ANY($1))
  AND m.gtgd20 >= $2
ORDER BY s.symbol
"""


class DbStockRepositoryImpl(StockRepository):
    async def list_stocks(self, exchanges: set[str] | None = None, min_gtgd: float = 0.0) -> list[Stock]:
        now = datetime.now(tz=timezone(timedelta(hours=7)))
        expected_fraction = _get_expected_fraction_at_time(now.hour, now.minute)

        pool: asyncpg.Pool = get_pool()
        exchanges_list = list(exchanges) if exchanges else None

        log.info("list_stocks (DB): exchanges=%s min_gtgd=%s fraction=%.2f", exchanges, min_gtgd, expected_fraction)

        rows = await pool.fetch(_QUERY, exchanges_list, min_gtgd)

        result = []
        for row in rows:
            gtgd20 = float(row["gtgd20"]) if row["gtgd20"] is not None else 0.0
            result.append(Stock(
                symbol=row["symbol"],
                exchange=row["exchange"],
                status=row["status"],
                price=float(row["current_price"]) if row["current_price"] is not None else 0.0,
                gtgd20=gtgd20,
                history_sessions=row["history_sessions"] or 0,
                today_value=float(row["today_value"]),
                avg_intraday_expected=gtgd20 * expected_fraction,
                intraday_ratio=float(row["today_value"]) / (gtgd20 * expected_fraction) if gtgd20 * expected_fraction > 0 else None,
            ))

        log.info("list_stocks (DB) done: %d stocks returned", len(result))
        return result
