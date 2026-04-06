from fastapi import APIRouter, BackgroundTasks, HTTPException
from infrastructure.market_data.state import get_state
from logger import get_logger

log = get_logger(__name__)
router = APIRouter()


@router.post("/crawler/start")
async def start_crawler(background_tasks: BackgroundTasks, history_days: int = 90):
    state = get_state()
    if state.status == "running":
        raise HTTPException(status_code=409, detail="Crawler is already running")

    from infrastructure.market_data.provider import run_full_crawl
    background_tasks.add_task(run_full_crawl, history_days)
    log.info("Crawler started via API")
    return {"message": "Crawler started"}


@router.get("/crawler/status")
async def crawler_status():
    state = get_state()
    return {
        "status": state.status,
        "started_at": state.started_at,
        "finished_at": state.finished_at,
        "total": state.total,
        "processed": state.processed,
        "current_symbol": state.current_symbol,
        "error": state.error,
        "failed_count": len(state.failed_symbols),
    }
