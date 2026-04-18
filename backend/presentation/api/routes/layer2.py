from fastapi import APIRouter, HTTPException

from infrastructure.container import get_layer2_usecase
from logger import get_logger

log = get_logger(__name__)
router = APIRouter()


@router.get("/layer2/latest")
async def get_latest():
    """Return cached Layer 2 scores plus seconds until next scheduled refresh."""
    try:
        return await get_layer2_usecase().get_latest()
    except Exception as e:
        log.error("get_latest failed", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
