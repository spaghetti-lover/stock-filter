import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Awaitable, Callable
from zoneinfo import ZoneInfo

from domain.repositories.layer1_repository import Layer1ResultRepository
from domain.repositories.layer2_repository import Layer2ScoreRepository
from application.dto.stock_dto import Layer2Response, Layer2StockScore
from utils.layer2 import cal_buy_score_detailed
from logger import get_logger

log = get_logger(__name__)

_executor = ThreadPoolExecutor(max_workers=30)
_CONCURRENCY = 10

ProgressCallback = Callable[[int, int, str], Awaitable[None]]


class Layer1NotRunError(Exception):
    pass


class Layer2UseCase:
    def __init__(
        self,
        layer1_repo: Layer1ResultRepository,
        layer2_repo: Layer2ScoreRepository,
        get_trading_history_fn,
        get_intraday_fn,
        get_vnindex_history_fn,
    ):
        self.layer1_repo = layer1_repo
        self.layer2_repo = layer2_repo
        self.get_trading_history = get_trading_history_fn
        self.get_intraday = get_intraday_fn
        self.get_vnindex_history = get_vnindex_history_fn

    async def execute(
        self,
        force_refresh: bool = False,
        on_progress: ProgressCallback | None = None,
    ) -> Layer2Response:
        # 1. Check Layer 1 results exist
        if not await self.layer1_repo.has_results():
            raise Layer1NotRunError("Run Layer 1 hard filter first")

        # 2. Return cached if available and not force_refresh
        if not force_refresh and await self.layer2_repo.has_scores():
            log.info("Layer2: returning cached scores")
            rows = await self.layer2_repo.get_scores()
            scores = [
                Layer2StockScore(
                    symbol=r["symbol"],
                    exchange=r["exchange"],
                    buy_score=r["buy_score"],
                    liquidity_score=r["liquidity_score"],
                    momentum_score=r["momentum_score"],
                    breakout_score=r["breakout_score"],
                    scored_at=r["scored_at"].isoformat(),
                )
                for r in rows
            ]
            latest = max(r["scored_at"] for r in rows) if rows else None
            return Layer2Response(
                scores=scores,
                from_cache=True,
                scored_at=latest.isoformat() if latest else None,
            )

        # 3. Fetch live data and compute scores
        passed_symbols = await self.layer1_repo.get_passed_symbols()
        total = len(passed_symbols)
        log.info("Layer2: scoring %d passed symbols (force_refresh=%s)", total, force_refresh)

        # Fetch VN-Index history once
        loop = asyncio.get_event_loop()
        log.info("Layer2: fetching VN-Index history")
        vnindex_history = await loop.run_in_executor(
            _executor, self.get_vnindex_history, 100
        )
        log.info("Layer2: VN-Index history fetched (%d sessions)", len(vnindex_history))

        # Compute minutes_elapsed from VN time
        vn_now = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
        minutes_elapsed = self._compute_minutes_elapsed(vn_now.hour, vn_now.minute)
        log.info("Layer2: VN time %02d:%02d, minutes_elapsed=%.0f", vn_now.hour, vn_now.minute, minutes_elapsed)

        # Score each symbol concurrently
        sem = asyncio.Semaphore(_CONCURRENCY)
        results = []
        processed_count = 0
        counter_lock = asyncio.Lock()

        async def score_symbol(sym_info: dict):
            nonlocal processed_count
            async with sem:
                symbol = sym_info["symbol"]
                exchange = sym_info["exchange"]
                try:
                    history = await loop.run_in_executor(
                        _executor, self.get_trading_history, symbol, 100
                    )
                    intraday = await loop.run_in_executor(
                        _executor, self.get_intraday, symbol
                    )

                    if len(history) < 65:
                        log.warning("Layer2: %s has only %d sessions, skipping", symbol, len(history))
                        return

                    detail = cal_buy_score_detailed(
                        history, intraday, vnindex_history, minutes_elapsed
                    )
                    results.append({
                        "symbol": symbol,
                        "exchange": exchange,
                        "buy_score": detail["buy_score"],
                        "liquidity_score": detail["liquidity"],
                        "momentum_score": detail["momentum"],
                        "breakout_score": detail["breakout"],
                    })
                    log.debug("Layer2: %s scored — BUY=%.1f (L=%.1f M=%.1f B=%.1f)",
                              symbol, detail["buy_score"], detail["liquidity"],
                              detail["momentum"], detail["breakout"])
                except Exception:
                    log.warning("Layer2: failed to score %s", symbol, exc_info=True)

            async with counter_lock:
                processed_count += 1
                if on_progress:
                    await on_progress(processed_count, total, symbol)

        await asyncio.gather(*[score_symbol(s) for s in passed_symbols])

        # 4. Save to DB
        log.info("Layer2: scoring complete — %d/%d symbols scored, saving to DB", len(results), total)
        await self.layer2_repo.save_scores(results)

        # 5. Return response
        now_iso = datetime.now().isoformat()
        scores = [
            Layer2StockScore(
                symbol=r["symbol"],
                exchange=r["exchange"],
                buy_score=r["buy_score"],
                liquidity_score=r["liquidity_score"],
                momentum_score=r["momentum_score"],
                breakout_score=r["breakout_score"],
                scored_at=now_iso,
            )
            for r in sorted(results, key=lambda x: x["buy_score"], reverse=True)
        ]
        log.info("Layer2: returning %d scores (freshly computed)", len(scores))

        return Layer2Response(
            scores=scores,
            from_cache=False,
            scored_at=now_iso,
        )

    @staticmethod
    def _compute_minutes_elapsed(hour: int, minute: int) -> float:
        """Compute trading minutes elapsed based on VN market schedule.

        Morning: 9:00-11:30 (150 min), Afternoon: 13:00-14:45 (105 min).
        Total: 255 minutes. Using 225 to match layer2.py convention (excludes ATO/ATC).
        """
        if hour < 9:
            return 0.0
        if hour < 11 or (hour == 11 and minute <= 30):
            return (hour - 9) * 60 + minute
        if hour < 13:
            return 150.0  # morning session done
        if hour < 14 or (hour == 14 and minute <= 45):
            return 150.0 + (hour - 13) * 60 + minute
        return 225.0  # full day
