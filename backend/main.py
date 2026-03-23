# main.py

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from presentation.api.routes import stock

app = FastAPI()

# 👇 register router
app.include_router(stock.router, tags=["Stock"])