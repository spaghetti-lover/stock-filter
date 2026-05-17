import asyncio

from fastapi import APIRouter

from infrastructure.container import get_discussion_crawl_usecase

router = APIRouter(prefix="/discussions")


@router.post("/crawl/trigger")
async def trigger_discussion_crawl():
    uc = get_discussion_crawl_usecase()
    asyncio.create_task(uc.execute())
    return {"status": "discussion crawl started"}


@router.get("/crawl/status")
async def get_discussion_crawl_status():
    uc = get_discussion_crawl_usecase()
    return await uc.get_status()
