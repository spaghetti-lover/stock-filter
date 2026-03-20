from fastapi import APIRouter, Depends
from application.use_case.get_stock import GetStockUseCase
from application.dto.stock_dto import GetStockResponse
from infrastructure.stock_repository_impl import StockRepositoryImpl

router = APIRouter()


def get_usecase() -> GetStockUseCase:
    return GetStockUseCase(StockRepositoryImpl())


@router.get("/stocks", response_model=list[GetStockResponse])
def get_stock(usecase: GetStockUseCase = Depends(get_usecase)):
    return usecase.execute()