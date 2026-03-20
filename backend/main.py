# main.py

from fastapi import FastAPI
from presentation.api.routes import stock

app = FastAPI()

# 👇 register router
app.include_router(stock.router, tags=["Stock"])