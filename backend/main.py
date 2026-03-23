# main.py

from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent.parent / ".env")

from logger import setup_logging, get_logger
setup_logging(latest_only=True)

from contextlib import asynccontextmanager
from fastapi import FastAPI
from presentation.api.routes import stock

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Server started")
    yield
    log.info("Server shutting down")


app = FastAPI(lifespan=lifespan)
app.include_router(stock.router, tags=["Stock"])