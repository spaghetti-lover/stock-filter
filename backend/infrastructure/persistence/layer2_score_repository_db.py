from datetime import datetime, timezone

from db.connection import get_pool
from domain.entities.layer2_score import Layer2Score
from domain.repositories.layer2_score_repository import Layer2ScoreRepository


class Layer2ScoreRepositoryDB(Layer2ScoreRepository):
    async def get_cached_scores(self) -> tuple[list[Layer2Score], str | None]:
        pool = get_pool()
        rows = await pool.fetch(
            "SELECT symbol, exchange, buy_score, liquidity_score, "
            "momentum_score, breakout_score, scored_at "
            "FROM layer2_scores ORDER BY buy_score DESC"
        )
        if not rows:
            return [], None
        scores = [
            Layer2Score(
                symbol=r["symbol"],
                exchange=r["exchange"],
                buy_score=r["buy_score"],
                liquidity_score=r["liquidity_score"],
                momentum_score=r["momentum_score"],
                breakout_score=r["breakout_score"],
            )
            for r in rows
        ]
        scored_at = rows[0]["scored_at"].isoformat()
        return scores, scored_at

    async def get_passed_symbols(self) -> list[dict]:
        pool = get_pool()
        rows = await pool.fetch(
            "SELECT symbol, exchange FROM stock_metrics WHERE passed = TRUE"
        )
        return [{"symbol": r["symbol"], "exchange": r["exchange"]} for r in rows]

    async def save_scores(self, scores: list[Layer2Score]) -> None:
        pool = get_pool()
        now = datetime.now(tz=timezone.utc)
        async with pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("TRUNCATE layer2_scores")
                await conn.executemany(
                    "INSERT INTO layer2_scores "
                    "(symbol, exchange, buy_score, liquidity_score, "
                    "momentum_score, breakout_score, scored_at) "
                    "VALUES ($1, $2, $3, $4, $5, $6, $7)",
                    [
                        (
                            s.symbol, s.exchange, s.buy_score,
                            s.liquidity_score, s.momentum_score,
                            s.breakout_score, now,
                        )
                        for s in scores
                    ],
                )
