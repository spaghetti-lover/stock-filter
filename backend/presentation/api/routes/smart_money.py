from fastapi import APIRouter, HTTPException, Query

from infrastructure.container import get_smart_money_flow_usecase
from logger import get_logger

log = get_logger(__name__)
router = APIRouter()


@router.get("/layer2/smart-money/{symbol}")
async def get_smart_money_flow(symbol: str, days: int = Query(60, ge=5, le=60)):
    """Per-day foreign + proprietary flow with spec-derived signals.

    Returns 200 with `rows: []` if the symbol has no flow data; 502 on
    upstream (vnstock) failure.
    """
    try:
        return await get_smart_money_flow_usecase().get_flow(symbol.upper(), days)
    except HTTPException:
        raise
    except Exception:
        log.error("smart_money_flow failed: symbol=%s days=%d", symbol, days, exc_info=True)
        raise HTTPException(status_code=502, detail="upstream flow data unavailable")
