"""Persistence for computed Layer 1 stock metrics.

Full-replace semantics: every call truncates ``stock_metrics`` and re-inserts
the supplied batch. The Layer 1 / crawl pipelines compute everything fresh
each run, so this is the natural boundary.
"""

from datetime import datetime, timezone

from db.connection import get_pool
from domain.entities.stock import Stock


async def save_stocks_to_db(
    stocks: list[Stock],
    passed_symbols: set[str] | None = None,
) -> None:
    """Truncate ``stock_metrics`` and batch-insert all stocks.

    When *passed_symbols* is provided, the ``passed`` column is set to True
    for symbols in the set so Layer 2 can pick them up.
    """
    passed = passed_symbols or set()
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("TRUNCATE stock_metrics")
            now = datetime.now(tz=timezone.utc)
            await conn.executemany(
                """INSERT INTO stock_metrics
                   (symbol, exchange, status, price, gtgd20, history_sessions,
                    today_value, avg_intraday_expected, intraday_ratio,
                    is_ceiling, is_floor, cv, crawled_at, passed)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14)""",
                [
                    (
                        s.symbol, s.exchange, s.status, s.price, s.gtgd20,
                        s.history_sessions, s.today_value, s.avg_intraday_expected,
                        s.intraday_ratio, s.is_ceiling, s.is_floor, s.cv, now,
                        s.symbol in passed,
                    )
                    for s in stocks
                ],
            )
