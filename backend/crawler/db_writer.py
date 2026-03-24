from datetime import date, datetime, time as dtime

import asyncpg

from db.connection import get_pool
from logger import get_logger

log = get_logger(__name__)


async def write_symbols(symbols: list[dict]):
    """Upsert symbol rows. Each dict must have 'symbol' and 'exchange'."""
    pool: asyncpg.Pool = get_pool()
    rows = [(s["symbol"], s["exchange"]) for s in symbols]
    async with pool.acquire() as conn:
        await conn.executemany(
            """
            INSERT INTO symbols (symbol, exchange, crawled_at)
            VALUES ($1, $2, now())
            ON CONFLICT (symbol) DO UPDATE
                SET exchange   = EXCLUDED.exchange,
                    crawled_at = EXCLUDED.crawled_at
            """,
            rows,
        )
    log.info("write_symbols: upserted %d rows", len(rows))


async def write_trading_history(symbol: str, history: list[dict]):
    """Upsert OHLCV rows for a symbol.

    Each dict is expected to have keys: time (or date), open, high, low, close, volume.
    """
    if not history:
        return

    pool: asyncpg.Pool = get_pool()
    rows = []
    for r in history:
        trade_date = r.get("time") or r.get("date")
        if isinstance(trade_date, str):
            trade_date = date.fromisoformat(trade_date)
        elif isinstance(trade_date, datetime):
            trade_date = trade_date.date()
        rows.append((
            symbol,
            trade_date,
            r.get("open"),
            r.get("high"),
            r.get("low"),
            r["close"],
            int(r["volume"]),
        ))

    async with pool.acquire() as conn:
        await conn.executemany(
            """
            INSERT INTO trading_history (symbol, trade_date, open, high, low, close, volume, crawled_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, now())
            ON CONFLICT (symbol, trade_date) DO UPDATE
                SET open       = EXCLUDED.open,
                    high       = EXCLUDED.high,
                    low        = EXCLUDED.low,
                    close      = EXCLUDED.close,
                    volume     = EXCLUDED.volume,
                    crawled_at = EXCLUDED.crawled_at
            """,
            rows,
        )
    log.debug("write_trading_history: upserted %d rows for %s", len(rows), symbol)


async def write_stock_metrics(
    symbol: str,
    current_price: float,
    gtgd20: float,
    history_sessions: int,
    metrics_date: date,
):
    """Upsert pre-computed metrics for a symbol."""
    pool: asyncpg.Pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO stock_metrics (symbol, current_price, gtgd20, history_sessions, metrics_date, crawled_at)
            VALUES ($1, $2, $3, $4, $5, now())
            ON CONFLICT (symbol) DO UPDATE
                SET current_price    = EXCLUDED.current_price,
                    gtgd20           = EXCLUDED.gtgd20,
                    history_sessions = EXCLUDED.history_sessions,
                    metrics_date     = EXCLUDED.metrics_date,
                    crawled_at       = EXCLUDED.crawled_at
            """,
            symbol, current_price, gtgd20, history_sessions, metrics_date,
        )
    log.debug("write_stock_metrics: upserted %s", symbol)


async def write_intraday(symbol: str, snap_date: date, intraday: list[dict]):
    """Upsert intraday snapshots and update the daily aggregate.

    Each dict must have 'time' (HH:MM:SS string or time obj), 'price', 'volume'.
    """
    if not intraday:
        return

    pool: asyncpg.Pool = get_pool()
    snapshot_rows = []
    today_value = 0.0

    for r in intraday:
        snap_time = r.get("time")
        if isinstance(snap_time, str):
            snap_time = dtime.fromisoformat(snap_time)
        price = float(r["price"])
        volume = int(r["volume"])
        today_value += price * volume
        snapshot_rows.append((symbol, snap_date, snap_time, price, volume))

    async with pool.acquire() as conn:
        await conn.executemany(
            """
            INSERT INTO intraday_snapshots (symbol, snap_date, snap_time, price, volume, crawled_at)
            VALUES ($1, $2, $3, $4, $5, now())
            ON CONFLICT DO NOTHING
            """,
            snapshot_rows,
        )
        await conn.execute(
            """
            INSERT INTO intraday_daily (symbol, snap_date, today_value, crawled_at)
            VALUES ($1, $2, $3, now())
            ON CONFLICT (symbol, snap_date) DO UPDATE
                SET today_value = EXCLUDED.today_value,
                    crawled_at  = EXCLUDED.crawled_at
            """,
            symbol, snap_date, today_value,
        )
    log.debug("write_intraday: %d snapshots, today_value=%.0f for %s", len(snapshot_rows), today_value, symbol)
