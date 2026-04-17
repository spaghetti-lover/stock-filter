import asyncio
import json

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from infrastructure.container import get_layer2_usecase
from logger import get_logger

log = get_logger(__name__)
router = APIRouter()


@router.get("/layer2/stream")
async def stream_layer2(refresh: bool = Query(default=False)):
    """Stream Layer 2 BUY score computation with progress events (SSE)."""
    usecase = get_layer2_usecase()
    queue: asyncio.Queue[str | None] = asyncio.Queue()

    async def on_progress(processed: int, total: int, symbol: str) -> None:
        event = json.dumps({"type": "progress", "processed": processed, "total": total, "symbol": symbol})
        await queue.put(f"data: {event}\n\n")

    async def run() -> None:
        try:
            result = await usecase.execute(refresh=refresh, on_progress=on_progress)
            payload = json.dumps({"type": "result", "data": result})
            await queue.put(f"data: {payload}\n\n")
        except ValueError as e:
            error = json.dumps({"type": "error", "code": 422, "detail": str(e)})
            await queue.put(f"data: {error}\n\n")
        except Exception as e:
            log.error("stream_layer2 failed", exc_info=True)
            error = json.dumps({"type": "error", "code": 500, "detail": str(e)})
            await queue.put(f"data: {error}\n\n")
        finally:
            await queue.put(None)

    async def event_generator():
        task = asyncio.create_task(run())
        while True:
            item = await queue.get()
            if item is None:
                break
            yield item
        await task

    return StreamingResponse(event_generator(), media_type="text/event-stream")
