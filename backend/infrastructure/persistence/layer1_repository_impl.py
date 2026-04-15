from datetime import datetime, timezone

from db.connection import get_pool
from domain.repositories.layer1_repository import Layer1ResultRepository
from logger import get_logger

log = get_logger(__name__)


class Layer1ResultRepositoryImpl(Layer1ResultRepository):

    async def save_results(
        self,
        passed: list[dict],
        rejected: list[dict],
    ) -> None:
        pool = get_pool()
        now = datetime.now(tz=timezone.utc)

        rows = []
        for s in passed:
            rows.append(self._to_row(s, "passed", None, now))
        for s in rejected:
            rows.append(self._to_row(s, "rejected", s.get("reject_reason"), now))

        async with pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("TRUNCATE layer1_results")
                if rows:
                    await conn.executemany(
                        """INSERT INTO layer1_results
                           (symbol, exchange, status, current_price, gtgd20,
                            history_sessions, today_value, avg_intraday_expected,
                            intraday_ratio, is_ceiling, is_floor, cv,
                            result, reject_reason, filtered_at)
                           VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15)""",
                        rows,
                    )
        log.info(
            "Saved layer1_results: %d passed, %d rejected",
            len(passed), len(rejected),
        )

    async def get_passed_symbols(self) -> list[dict]:
        pool = get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT symbol, exchange FROM layer1_results WHERE result = $1",
                "passed",
            )
        return [dict(r) for r in rows]

    async def has_results(self) -> bool:
        pool = get_pool()
        async with pool.acquire() as conn:
            count = await conn.fetchval("SELECT count(*) FROM layer1_results")
        return count > 0

    @staticmethod
    def _to_row(s: dict, result: str, reject_reason: str | None, now: datetime) -> tuple:
        return (
            s.get("symbol", ""),
            s.get("exchange", ""),
            s.get("status", "N/A"),
            s.get("current_price", 0.0),
            s.get("gtgd20", 0.0),
            s.get("history_sessions", 0),
            s.get("today_value", 0.0),
            s.get("avg_intraday_expected", 0.0),
            s.get("intraday_ratio"),
            s.get("is_ceiling", False),
            s.get("is_floor", False),
            s.get("cv"),
            result,
            reject_reason,
            now,
        )
