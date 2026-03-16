from fastapi import FastAPI
from app.config.settings import settings
from app.interfaces.api.screener_controller import router as screener_router

app = FastAPI(title=settings.app_name, debug=settings.debug)

app.include_router(screener_router, prefix=settings.api_prefix)


@app.get("/health")
def health():
    return {"status": "ok"}
