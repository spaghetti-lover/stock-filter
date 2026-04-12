import os
import asyncpg

_pool: asyncpg.Pool | None = None


async def init_pool():
    global _pool
    dsn = os.environ.get("DATABASE_URL", "postgresql://postgres:password@localhost:5432/stock_data")
    _pool = await asyncpg.create_pool(dsn, min_size=2, max_size=10)


async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Database pool not initialized. Call init_pool() first.")
    return _pool
