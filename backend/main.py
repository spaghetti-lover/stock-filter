# main.py

from dotenv import load_dotenv
load_dotenv()

from logger import setup_logging, get_logger
setup_logging()

from fastapi import FastAPI
from presentation.api.routes import stock

log = get_logger(__name__)

app = FastAPI()
app.include_router(stock.router, tags=["Stock"])


@app.on_event("startup")
async def on_startup():
    log.info("Server started")


@app.on_event("shutdown")
async def on_shutdown():
    log.info("Server shutting down")