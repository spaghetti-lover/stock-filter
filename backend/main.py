# main.py

from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent / ".env", override=False)

from logger import setup_logging, get_logger
setup_logging(latest_only=True)

import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from presentation.api.routes import layer1, layer2, chat, trading_agent, symbols, discussions
from db.connection import init_pool, close_pool
from infrastructure.scheduler.scheduler import start_scheduler, stop_scheduler
from infrastructure.container import (
    get_crawl_usecase,
    get_discussion_crawl_usecase,
    get_layer2_usecase,
    get_live_layer1_usecase,
)
from infrastructure.tools import McpToolRegistry

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pool()
    tool_registry = McpToolRegistry()
    await tool_registry.start()
    app.state.tool_registry = tool_registry
    crawl_usecase = get_crawl_usecase()
    layer1_usecase = get_live_layer1_usecase(save=True)
    layer2_usecase = get_layer2_usecase()
    discussion_usecase = get_discussion_crawl_usecase()

    async def layer1_run():
        await layer1_usecase.execute()

    async def layer2_refresh():
        await layer2_usecase.execute(refresh=True)

    start_scheduler(crawl_usecase.execute, layer1_run, layer2_refresh, discussion_usecase.execute)
    asyncio.create_task(layer2_refresh())
    log.info("App started: DB pool, MCP tool registry, and scheduler initialized")
    yield
    stop_scheduler()
    await tool_registry.stop()
    await close_pool()
    log.info("App shutdown: scheduler, tool registry, and DB pool closed")


app = FastAPI(lifespan=lifespan)

_default_origins = "http://localhost:3000"
_allow_origins = [
    o.strip() for o in os.environ.get("CORS_ALLOW_ORIGINS", _default_origins).split(",") if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(layer1.router, tags=["Layer 1"])
app.include_router(layer2.router, tags=["Layer 2"])
app.include_router(chat.router, tags=["Chat"])
app.include_router(trading_agent.router, tags=["Trading Agent"])
app.include_router(symbols.router, tags=["Symbols"])
app.include_router(discussions.router, tags=["Discussions"])