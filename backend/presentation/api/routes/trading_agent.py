from fastapi import APIRouter, HTTPException

from application.dto.trading_agent_dto import RunRequest, RunStartResponse, RunStatusResponse
from application.use_case.trading_agent_use_case import get_run, start_run

router = APIRouter(prefix="/trading-agent")


@router.post("/run", response_model=RunStartResponse)
async def run_pipeline(request: RunRequest) -> RunStartResponse:
    symbol = request.symbol.strip().upper()
    if not symbol:
        raise HTTPException(status_code=400, detail="symbol is required")
    run_id = start_run(symbol=symbol, horizon=request.horizon, provider=request.provider)
    return RunStartResponse(run_id=run_id)


@router.get("/status/{run_id}", response_model=RunStatusResponse)
async def run_status(run_id: str) -> RunStatusResponse:
    state = get_run(run_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"run {run_id} not found")
    return RunStatusResponse(**state)
