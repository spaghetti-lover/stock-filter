from datetime import datetime, timezone

from db.connection import get_pool
from domain.repositories.layer2_repository import Layer2ScoreRepository
from logger import get_logger

log = get_logger(__name__)


class Layer2ScoreRepositoryImpl(Layer2ScoreRepository):

    async def save_scores(self, scores: list[dict]) -> None:
        pool = get_pool()
        now = datetime.now(tz=timezone.utc)

        rows = [
            (
                s["symbol"],
                s["exchange"],
                s["buy_score"],
                s["liquidity_score"],
                s["momentum_score"],
                s["breakout_score"],
                now,
            )
            for s in scores
        ]

        async with pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("TRUNCATE layer2_scores")
                if rows:
                    await conn.executemany(
                        """INSERT INTO layer2_scores
                           (symbol, exchange, buy_score, liquidity_score,
                            momentum_score, breakout_score, scored_at)
                           VALUES ($1,$2,$3,$4,$5,$6,$7)""",
                        rows,
                    )
        log.info("Saved layer2_scores: %d stocks", len(scores))

    async def get_scores(self) -> list[dict]:
        pool = get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT symbol, exchange, buy_score, liquidity_score, "
                "momentum_score, breakout_score, scored_at "
                "FROM layer2_scores ORDER BY buy_score DESC"
            )
        return [dict(r) for r in rows]

    async def has_scores(self) -> bool:
        pool = get_pool()
        async with pool.acquire() as conn:
            count = await conn.fetchval("SELECT count(*) FROM layer2_scores")
        return count > 0
