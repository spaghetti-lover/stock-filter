import asyncio
import json

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from application.dto.stock_dto import FilteredStocksResponse, Layer2Response
from application.use_case.layer2_use_case import Layer1NotRunError
from infrastructure.container import get_live_stock_usecase, get_cached_stock_usecase, get_crawl_usecase, get_layer2_usecase
from logger import get_logger

log = get_logger(__name__)
router = APIRouter()


@router.get("/stocks", response_model=FilteredStocksResponse)
async def get_stock(
    exchanges: list[str] = Query(default=["HOSE", "HNX", "UPCOM"]),
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
    usecase = get_cached_stock_usecase()
    log.info("GET /stocks exchanges=%s min_gtgd=%s", exchanges, min_gtgd)
    try:
        result = await usecase.execute(
            exchanges=set(exchanges),
            min_gtgd=min_gtgd,
            statuses=set(statuses) if statuses else None,
            min_history=min_history,
            min_price=min_price,
            min_intraday_ratio=min_intraday_ratio,
            min_volume=min_volume,
            use_exchange=use_exchange,
            use_gtgd20=use_gtgd20,
            use_status=use_status,
            use_history=use_history,
            use_price=use_price,
            use_intraday=use_intraday,
            use_volume=use_volume,
            exclude_ceiling_floor=exclude_ceiling_floor,
            cv_cap=cv_cap,
            use_cv=use_cv,
            market_regime_gate=market_regime_gate,
        )
        log.info("GET /stocks -> %d passed, %d rejected", len(result.passed), len(result.rejected))
        return result
    except Exception as e:
        log.error("GET /stocks failed", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stocks/stream")
async def stream_stocks(
    exchanges: list[str] = Query(default=["HOSE", "HNX", "UPCOM"]),
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
    usecase = get_live_stock_usecase()
    queue: asyncio.Queue[str | None] = asyncio.Queue()

    async def on_progress(processed: int, total: int, symbol: str) -> None:
        event = json.dumps({"type": "progress", "processed": processed, "total": total, "symbol": symbol})
        await queue.put(f"data: {event}\n\n")

    async def run() -> None:
        try:
            result = await usecase.execute(
                exchanges=set(exchanges),
                min_gtgd=min_gtgd,
                statuses=set(statuses) if statuses else None,
                min_history=min_history,
                min_price=min_price,
                min_intraday_ratio=min_intraday_ratio,
                min_volume=min_volume,
                use_exchange=use_exchange,
                use_gtgd20=use_gtgd20,
                use_status=use_status,
                use_history=use_history,
                use_price=use_price,
                use_intraday=use_intraday,
                use_volume=use_volume,
                exclude_ceiling_floor=exclude_ceiling_floor,
                cv_cap=cv_cap,
                use_cv=use_cv,
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


@router.get("/stocks/layer2", response_model=Layer2Response)
async def get_layer2_scores(
    force_refresh: bool = Query(default=False),
):
    usecase = get_layer2_usecase()
    try:
        result = await usecase.execute(force_refresh=force_refresh)
        log.info("GET /stocks/layer2 -> %d scores, from_cache=%s", len(result.scores), result.from_cache)
        return result
    except Layer1NotRunError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log.error("GET /stocks/layer2 failed", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stocks/layer2/stream")
async def stream_layer2_scores():
    """SSE endpoint for Layer 2 scoring with progress updates."""
    usecase = get_layer2_usecase()
    queue: asyncio.Queue[str | None] = asyncio.Queue()

    async def on_progress(processed: int, total: int, symbol: str) -> None:
        event = json.dumps({"type": "progress", "processed": processed, "total": total, "symbol": symbol})
        await queue.put(f"data: {event}\n\n")

    async def run() -> None:
        try:
            result = await usecase.execute(force_refresh=True, on_progress=on_progress)
            payload = json.dumps({"type": "result", "data": result.model_dump()})
            await queue.put(f"data: {payload}\n\n")
        except Layer1NotRunError as e:
            error = json.dumps({"type": "error", "detail": str(e)})
            await queue.put(f"data: {error}\n\n")
        except Exception as e:
            log.error("GET /stocks/layer2/stream failed", exc_info=True)
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


@router.post("/crawl/trigger")
async def trigger_crawl():
    crawl = get_crawl_usecase()
    asyncio.create_task(crawl.execute())
    return {"status": "crawl started"}


@router.get("/crawl/status")
async def get_crawl_status():
    crawl = get_crawl_usecase()
    return await crawl.get_status()
