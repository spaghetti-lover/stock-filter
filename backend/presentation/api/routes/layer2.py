from fastapi import APIRouter
from pydantic import BaseModel
from logger import get_logger

log = get_logger(__name__)
router = APIRouter()


class Layer2ScoreItem(BaseModel):
    symbol: str
    exchange: str
    buy_score: float
    liquidity_score: float
    momentum_score: float
    breakout_score: float


class Layer2Response(BaseModel):
    scores: list[Layer2ScoreItem]
    from_cache: bool = False
    scored_at: str | None = None


@router.get("/layer2", response_model=Layer2Response)
async def get_layer2():
    """Stub endpoint — returns fake data. Will be implemented later."""
    log.info("GET /layer2 (stub)")
    return Layer2Response(
        scores=[
            Layer2ScoreItem(
                symbol="FAKE",
                exchange="HOSE",
                buy_score=0.0,
                liquidity_score=0.0,
                momentum_score=0.0,
                breakout_score=0.0,
            ),
        ],
        from_cache=False,
        scored_at=None,
    )
