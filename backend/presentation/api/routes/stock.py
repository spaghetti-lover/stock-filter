from fastapi import APIRouter, Depends, HTTPException, Query
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
        )
        log.info("GET /stocks -> %d passed, %d rejected", len(result.passed), len(result.rejected))
        return result
    except Exception as e:
        log.error("GET /stocks failed", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
