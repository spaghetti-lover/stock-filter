import asyncio
import json

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from application.dto.stock_dto import FilteredStocksResponse
from application.layer1 import FilterCriteria
from infrastructure.container import get_live_layer1_usecase, get_cached_layer1_usecase
from logger import get_logger

log = get_logger(__name__)
router = APIRouter()


def _build_criteria(
    exchanges: list[str],
    min_gtgd: float,
    statuses: list[str] | None,
    min_history: int,
    min_price: float,
    min_intraday_ratio: float,
    min_volume: float,
    use_exchange: bool,
    use_gtgd20: bool,
    use_status: bool,
    use_history: bool,
    use_price: bool,
    use_intraday: bool,
    use_volume: bool,
    exclude_ceiling_floor: bool,
    cv_cap: float,
    use_cv: bool,
) -> FilterCriteria:
    """Translate route-level query params (billions, thousands, on/off flags)
    into a canonical-units FilterCriteria. None means rule disabled."""
    return FilterCriteria(
        exchanges=frozenset(exchanges) if use_exchange and exchanges else None,
        statuses=frozenset(statuses) if use_status and statuses else None,
        min_gtgd_vnd=min_gtgd * 1e9 if use_gtgd20 else None,
        min_history=min_history if use_history else None,
        min_price_vnd=min_price if use_price else None,
        min_intraday_ratio=min_intraday_ratio if use_intraday else None,
        min_volume_vnd=min_volume if use_volume else None,
        cv_cap_pct=cv_cap if use_cv else None,
        exclude_ceiling_floor=exclude_ceiling_floor,
    )


@router.get("/layer1", response_model=FilteredStocksResponse)
async def get_layer1(
    exchanges: list[str] = Query(default=["HOSE", "HNX"]),
    min_gtgd: float = Query(default=0.0, ge=0.0),
    statuses: list[str] | None = Query(default=None),
    min_history: int = Query(default=0, ge=0),
    min_price: float = Query(default=0.0, ge=0.0),
    min_intraday_ratio: float = Query(default=0.0, ge=0.0, le=1.0),
    min_volume: float = Query(default=0.0, ge=0.0),
    use_exchange: bool = Query(default=True),
    use_gtgd20: bool = Query(default=True),
    use_status: bool = Query(default=True),
    use_history: bool = Query(default=True),
    use_price: bool = Query(default=True),
    use_intraday: bool = Query(default=True),
    use_volume: bool = Query(default=True),
    exclude_ceiling_floor: bool = Query(default=True),
    cv_cap: float = Query(default=200.0, ge=0.0, le=1000.0),
    use_cv: bool = Query(default=True),
    market_regime_gate: bool = Query(default=True),
):
    usecase = get_cached_layer1_usecase()
    log.info("GET /layer1 exchanges=%s min_gtgd=%s", exchanges, min_gtgd)
    criteria = _build_criteria(
        exchanges, min_gtgd, statuses, min_history, min_price, min_intraday_ratio, min_volume,
        use_exchange, use_gtgd20, use_status, use_history, use_price, use_intraday, use_volume,
        exclude_ceiling_floor, cv_cap, use_cv,
    )
    try:
        result = await usecase.execute(criteria=criteria, market_regime_gate=market_regime_gate)
        log.info("GET /layer1 -> %d passed, %d rejected", len(result.passed), len(result.rejected))
        return result
    except Exception as e:
        log.error("GET /layer1 failed", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/layer1/stream")
async def stream_layer1(
    exchanges: list[str] = Query(default=["HOSE", "HNX"]),
    min_gtgd: float = Query(default=0.0, ge=0.0),
    statuses: list[str] | None = Query(default=None),
    min_history: int = Query(default=0, ge=0),
    min_price: float = Query(default=0.0, ge=0.0),
    min_intraday_ratio: float = Query(default=0.0, ge=0.0, le=1.0),
    min_volume: float = Query(default=0.0, ge=0.0),
    use_exchange: bool = Query(default=True),
    use_gtgd20: bool = Query(default=True),
    use_status: bool = Query(default=True),
    use_history: bool = Query(default=True),
    use_price: bool = Query(default=True),
    use_intraday: bool = Query(default=True),
    use_volume: bool = Query(default=True),
    exclude_ceiling_floor: bool = Query(default=True),
    cv_cap: float = Query(default=200.0, ge=0.0, le=1000.0),
    use_cv: bool = Query(default=True),
    market_regime_gate: bool = Query(default=True),
):
    usecase = get_live_layer1_usecase(save=True)
    criteria = _build_criteria(
        exchanges, min_gtgd, statuses, min_history, min_price, min_intraday_ratio, min_volume,
        use_exchange, use_gtgd20, use_status, use_history, use_price, use_intraday, use_volume,
        exclude_ceiling_floor, cv_cap, use_cv,
    )
    queue: asyncio.Queue[str | None] = asyncio.Queue()

    async def on_progress(processed: int, total: int, symbol: str) -> None:
        event = json.dumps({"type": "progress", "processed": processed, "total": total, "symbol": symbol})
        await queue.put(f"data: {event}\n\n")

    async def run() -> None:
        try:
            result = await usecase.execute(
                criteria=criteria,
                market_regime_gate=market_regime_gate,
                on_progress=on_progress,
            )
            payload = json.dumps({"type": "result", "data": result.model_dump()})
            await queue.put(f"data: {payload}\n\n")
        except Exception as e:
            error = json.dumps({"type": "error", "detail": str(e)})
            await queue.put(f"data: {error}\n\n")
        finally:
            await queue.put(None)

    async def event_generator():
        task = asyncio.create_task(run())
        while True:
            item = await queue.get()
            if item is None:
                break
            yield item
        await task

    return StreamingResponse(event_generator(), media_type="text/event-stream")
