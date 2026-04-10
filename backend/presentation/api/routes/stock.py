import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from application.use_case.get_stock import GetStockUseCase
from application.dto.stock_dto import FilteredStocksResponse
from infrastructure.stock_repository_impl import StockRepositoryImpl
from logger import get_logger

log = get_logger(__name__)
router = APIRouter()


def get_usecase() -> GetStockUseCase:
    return GetStockUseCase(StockRepositoryImpl())


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
    usecase: GetStockUseCase = Depends(get_usecase),
):
    log.info("GET /stocks exchanges=%s min_gtgd=%s statuses=%s", exchanges, min_gtgd, statuses)
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


def _stock_query_params(
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
) -> dict:
    return dict(
        exchanges=exchanges, min_gtgd=min_gtgd, statuses=statuses,
        min_history=min_history, min_price=min_price,
        min_intraday_ratio=min_intraday_ratio, min_volume=min_volume,
        use_exchange=use_exchange, use_gtgd20=use_gtgd20, use_status=use_status,
        use_history=use_history, use_price=use_price,
        use_intraday=use_intraday, use_volume=use_volume,
        exclude_ceiling_floor=exclude_ceiling_floor,
        cv_cap=cv_cap, use_cv=use_cv, market_regime_gate=market_regime_gate,
    )


@router.get("/stocks/stream")
async def stream_stocks(
    params: dict = Depends(_stock_query_params),
    usecase: GetStockUseCase = Depends(get_usecase),
):
    queue: asyncio.Queue[str | None] = asyncio.Queue()

    async def on_progress(processed: int, total: int, symbol: str) -> None:
        event = json.dumps({"type": "progress", "processed": processed, "total": total, "symbol": symbol})
        await queue.put(f"data: {event}\n\n")

    async def run() -> None:
        try:
            result = await usecase.execute(
                exchanges=set(params["exchanges"]),
                min_gtgd=params["min_gtgd"],
                statuses=set(params["statuses"]) if params["statuses"] else None,
                min_history=params["min_history"],
                min_price=params["min_price"],
                min_intraday_ratio=params["min_intraday_ratio"],
                min_volume=params["min_volume"],
                use_exchange=params["use_exchange"],
                use_gtgd20=params["use_gtgd20"],
                use_status=params["use_status"],
                use_history=params["use_history"],
                use_price=params["use_price"],
                use_intraday=params["use_intraday"],
                use_volume=params["use_volume"],
                exclude_ceiling_floor=params["exclude_ceiling_floor"],
                cv_cap=params["cv_cap"],
                use_cv=params["use_cv"],
                market_regime_gate=params["market_regime_gate"],
                on_progress=on_progress,
            )
            payload = json.dumps({"type": "result", "data": result.model_dump()})
            await queue.put(f"data: {payload}\n\n")
        except Exception as e:
            error = json.dumps({"type": "error", "detail": str(e)})
            await queue.put(f"data: {error}\n\n")
        finally:
            await queue.put(None)  # sentinel

    async def event_generator():
        task = asyncio.create_task(run())
        while True:
            item = await queue.get()
            if item is None:
                break
            yield item
        await task

    return StreamingResponse(event_generator(), media_type="text/event-stream")
