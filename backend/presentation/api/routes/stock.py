from fastapi import APIRouter, Depends, Query
from application.use_case.get_stock import GetStockUseCase
from application.dto.stock_dto import GetStockResponse
from infrastructure.db_stock_repository_impl import DbStockRepositoryImpl
from logger import get_logger

log = get_logger(__name__)
router = APIRouter()


def get_usecase() -> GetStockUseCase:
    return GetStockUseCase(DbStockRepositoryImpl())


@router.get("/stocks", response_model=list[GetStockResponse])
async def get_stock(
    exchanges: list[str] = Query(default=["HOSE", "HNX", "UPCOM"]),
    min_gtgd: float = Query(default=0.0, ge=0.0),
    usecase: GetStockUseCase = Depends(get_usecase),
):
    log.info("GET /stocks exchanges=%s min_gtgd=%s", exchanges, min_gtgd)
    try:
        result = await usecase.execute(exchanges=set(exchanges), min_gtgd=min_gtgd)
        log.info("GET /stocks -> %d results", len(result))
        return result
    except BaseException:
        log.error("GET /stocks failed", exc_info=True)
        raise
