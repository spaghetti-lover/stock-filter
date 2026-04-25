import asyncio
from datetime import datetime, timezone

from domain.entities.layer2_score import Layer2Score
from domain.repositories.layer2_score_repository import Layer2ScoreRepository
from infrastructure.market_data.data import get_trading_history, get_intraday, get_vnindex_history
from infrastructure.persistence.stock_metrics import executor, CONCURRENCY, get_expected_fraction_at_time
from utils.layer2 import cal_buy_score
from logger import get_logger

log = get_logger(__name__)

REFRESH_INTERVAL_SECONDS = 300


class Layer2UseCase:
    def __init__(self, repo: Layer2ScoreRepository):
        self.repo = repo

    async def execute(self, refresh: bool = False) -> dict:
        if not refresh:
            cached, scored_at = await self.repo.get_cached_scores()
            if cached:
                log.info("Returning %d cached Layer 2 scores", len(cached))
                return self._build_response(cached, scored_at=scored_at)

        symbols = await self.repo.get_passed_symbols()
        if not symbols:
            raise ValueError("No Layer 1 data found. Please run Layer 1 filter first.")

        log.info("Computing Layer 2 scores for %d passed symbols", len(symbols))

        loop = asyncio.get_event_loop()
        vnindex_history = await loop.run_in_executor(executor, get_vnindex_history, 100)
        if not vnindex_history:
            raise ValueError("Could not fetch VN-Index history.")

        now = datetime.now()
        fraction = get_expected_fraction_at_time(now.hour, now.minute)
        minutes_elapsed = fraction * 225

        sem = asyncio.Semaphore(CONCURRENCY)

        async def process(item: dict) -> Layer2Score | None:
            symbol = item["symbol"]
            exchange = item["exchange"]
            async with sem:
                try:
                    history_fut = loop.run_in_executor(executor, get_trading_history, symbol, 100)
                    intraday_fut = loop.run_in_executor(executor, get_intraday, symbol)
                    history, intraday = await asyncio.gather(history_fut, intraday_fut)

                    if len(history) < 65:
                        log.warning("Skipping %s: only %d sessions (need 65)", symbol, len(history))
                        return None
                    result = cal_buy_score(history, intraday, vnindex_history, minutes_elapsed)
                    return Layer2Score(
                        symbol=symbol,
                        exchange=exchange,
                        buy_score=result.buy_score,
                        liquidity_score=result.liquidity_score,
                        momentum_score=result.momentum_score,
                        breakout_score=result.breakout_score,
                        breakdown={
                            "liquidity": result.liquidity,
                            "momentum": result.momentum,
                            "breakout": result.breakout,
                        },
                    )
                except Exception:
                    log.warning("Failed to score %s", symbol, exc_info=True)
                    return None

        results = await asyncio.gather(*[process(item) for item in symbols])
        scores = [r for r in results if r is not None]
        scores.sort(key=lambda s: s.buy_score, reverse=True)

        log.info("Scored %d/%d symbols", len(scores), len(symbols))

        if scores:
            await self.repo.save_scores(scores)

        scored_at = datetime.now(tz=timezone.utc).isoformat()
        return self._build_response(scores, scored_at=scored_at)

    async def get_latest(self) -> dict:
        scores, scored_at = await self.repo.get_cached_scores()
        return self._build_response(scores, scored_at=scored_at)

    def _build_response(self, scores: list[Layer2Score], scored_at: str | None) -> dict:
        return {
            "scores": [
                {
                    "symbol": s.symbol,
                    "exchange": s.exchange,
                    "buy_score": s.buy_score,
                    "liquidity_score": s.liquidity_score,
                    "momentum_score": s.momentum_score,
                    "breakout_score": s.breakout_score,
                    "breakdown": s.breakdown,
                }
                for s in scores
            ],
            "scored_at": scored_at,
            "next_refresh_in": _compute_next_refresh_in(scored_at),
        }


def _compute_next_refresh_in(scored_at: str | None) -> int:
    if not scored_at:
        return REFRESH_INTERVAL_SECONDS
    try:
        dt = datetime.fromisoformat(scored_at)
    except ValueError:
        return REFRESH_INTERVAL_SECONDS
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    elapsed = (datetime.now(tz=timezone.utc) - dt).total_seconds()
    remaining = REFRESH_INTERVAL_SECONDS - (elapsed % REFRESH_INTERVAL_SECONDS)
    return max(0, min(REFRESH_INTERVAL_SECONDS, int(remaining)))
