import asyncio
from datetime import datetime, timezone
from typing import Awaitable, Callable

from domain.entities.layer2_score import Layer2Score
from domain.repositories.layer2_score_repository import Layer2ScoreRepository
from infrastructure.market_data.data import get_trading_history, get_intraday, get_vnindex_history
from infrastructure.persistence.stock_metrics import executor, CONCURRENCY, get_expected_fraction_at_time
from utils.layer2 import cal_buy_score
from logger import get_logger

log = get_logger(__name__)

ProgressCallback = Callable[[int, int, str], Awaitable[None]]


class Layer2UseCase:
    def __init__(self, repo: Layer2ScoreRepository):
        self.repo = repo

    async def execute(self, refresh: bool = False, on_progress: ProgressCallback | None = None) -> dict:
        # 1. Return cached scores if available and not refreshing
        if not refresh:
            cached, scored_at = await self.repo.get_cached_scores()
            if cached:
                log.info("Returning %d cached Layer 2 scores", len(cached))
                return self._build_response(cached, from_cache=True, scored_at=scored_at)

        # 2. Get passed symbols from Layer 1
        symbols = await self.repo.get_passed_symbols()
        if not symbols:
            raise ValueError("No Layer 1 data found. Please run Layer 1 filter first.")

        log.info("Computing Layer 2 scores for %d passed symbols", len(symbols))

        # 3. Fetch VN-Index history once (shared across all symbols)
        loop = asyncio.get_event_loop()
        vnindex_history = await loop.run_in_executor(executor, get_vnindex_history, 100)
        if not vnindex_history:
            raise ValueError("Could not fetch VN-Index history.")

        # 4. Compute minutes_elapsed
        now = datetime.now()
        fraction = get_expected_fraction_at_time(now.hour, now.minute)
        minutes_elapsed = fraction * 225

        # 5. Compute scores concurrently
        sem = asyncio.Semaphore(CONCURRENCY)
        total = len(symbols)
        processed_count = 0
        counter_lock = asyncio.Lock()

        async def process(item: dict) -> Layer2Score | None:
            nonlocal processed_count
            symbol = item["symbol"]
            exchange = item["exchange"]
            async with sem:
                try:
                    history_fut = loop.run_in_executor(executor, get_trading_history, symbol, 100)
                    intraday_fut = loop.run_in_executor(executor, get_intraday, symbol)
                    history, intraday = await asyncio.gather(history_fut, intraday_fut)

                    if len(history) < 65:
                        log.warning("Skipping %s: only %d sessions (need 65)", symbol, len(history))
                        score = None
                    else:
                        result = cal_buy_score(history, intraday, vnindex_history, minutes_elapsed)
                        score = Layer2Score(
                            symbol=symbol,
                            exchange=exchange,
                            buy_score=result.buy_score,
                            liquidity_score=result.liquidity_score,
                            momentum_score=result.momentum_score,
                            breakout_score=result.breakout_score,
                        )
                except Exception:
                    log.warning("Failed to score %s", symbol, exc_info=True)
                    score = None

            async with counter_lock:
                processed_count += 1
                if on_progress:
                    await on_progress(processed_count, total, symbol)

            return score

        results = await asyncio.gather(*[process(item) for item in symbols])
        scores = [r for r in results if r is not None]
        scores.sort(key=lambda s: s.buy_score, reverse=True)

        log.info("Scored %d/%d symbols", len(scores), len(symbols))

        # 6. Save to DB
        if scores:
            await self.repo.save_scores(scores)

        scored_at = datetime.now(tz=timezone.utc).isoformat()
        return self._build_response(scores, from_cache=False, scored_at=scored_at)

    def _build_response(self, scores: list[Layer2Score], from_cache: bool, scored_at: str | None) -> dict:
        return {
            "scores": [
                {
                    "symbol": s.symbol,
                    "exchange": s.exchange,
                    "buy_score": s.buy_score,
                    "liquidity_score": s.liquidity_score,
                    "momentum_score": s.momentum_score,
                    "breakout_score": s.breakout_score,
                }
                for s in scores
            ],
            "from_cache": from_cache,
            "scored_at": scored_at,
        }
