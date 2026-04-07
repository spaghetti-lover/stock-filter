# main.py

from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent / ".env")

from logger import setup_logging, get_logger
setup_logging(latest_only=True)

from fastapi import FastAPI
from presentation.api.routes import stock, chat

log = get_logger(__name__)

app = FastAPI()
app.include_router(stock.router, tags=["Stock"])
app.include_router(chat.router, tags=["Chat"])
