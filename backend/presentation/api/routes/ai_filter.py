from fastapi import APIRouter

from application.dto.ai_filter_dto import (
    AIFilterApplyRequest,
    AIFilterCatalogResponse,
    AIFilterParseRequest,
    AIFilterParseResponse,
)
from application.dto.stock_dto import FilteredStocksResponse
from application.services.ai_filter_catalog import public_catalog
from infrastructure.container import get_ai_filter_usecase

router = APIRouter(prefix="/ai-filter")


@router.get("/catalog", response_model=AIFilterCatalogResponse)
async def get_catalog() -> AIFilterCatalogResponse:
    return AIFilterCatalogResponse(entries=public_catalog())


@router.post("/parse", response_model=AIFilterParseResponse)
async def parse(request: AIFilterParseRequest) -> AIFilterParseResponse:
    usecase = get_ai_filter_usecase(request.provider)
    return await usecase.parse(request)


@router.post("/apply", response_model=FilteredStocksResponse)
async def apply(request: AIFilterApplyRequest) -> FilteredStocksResponse:
    usecase = get_ai_filter_usecase("claude")
    return await usecase.apply(request)
