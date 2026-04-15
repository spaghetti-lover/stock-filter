# main.py

from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent / ".env")

from logger import setup_logging, get_logger
setup_logging(latest_only=True)

from contextlib import asynccontextmanager
from fastapi import FastAPI
from presentation.api.routes import stock, chat
from db.connection import init_pool, close_pool
from infrastructure.scheduler.scheduler import start_scheduler, stop_scheduler
from infrastructure.container import get_crawl_usecase, get_layer2_usecase

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pool()
    crawl_usecase = get_crawl_usecase()
    layer2_usecase = get_layer2_usecase()

    async def layer2_refresh():
        await layer2_usecase.execute(force_refresh=True)

    start_scheduler(crawl_usecase.execute, layer2_refresh_fn=layer2_refresh)
    log.info("App started: DB pool and scheduler initialized")
    yield
    stop_scheduler()
    await close_pool()
    log.info("App shutdown: scheduler and DB pool closed")


app = FastAPI(lifespan=lifespan)
app.include_router(stock.router, tags=["Stock"])
app.include_router(chat.router, tags=["Chat"])
