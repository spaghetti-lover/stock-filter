import os

import asyncpg

from logger import get_logger

log = get_logger(__name__)

_pool: asyncpg.Pool | None = None


async def init_pool() -> asyncpg.Pool:
    global _pool
    dsn = os.environ["DATABASE_URL"]
    _pool = await asyncpg.create_pool(dsn=dsn, min_size=2, max_size=10)
    log.info("DB pool created")
    return _pool


async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        log.info("DB pool closed")


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("DB pool not initialised — call init_pool() first")
    return _pool
