"""Symbol catalog endpoint for HOSE/HNX/UPCOM (cached per day)."""

from __future__ import annotations

import asyncio
from datetime import date
from threading import Lock

from fastapi import APIRouter
from pydantic import BaseModel
from vnstock_data import Reference

from infrastructure.market_data.data import _limiter
from logger import get_logger


router = APIRouter()
log = get_logger(__name__)


class SymbolEntry(BaseModel):
    exchange: str
    symbol: str


_CACHE: dict[str, list[dict]] = {}
_CACHE_LOCK = Lock()
_ALLOWED = {"HOSE", "HNX", "UPCOM"}


def _fetch_symbols() -> list[dict]:
    today = date.today().isoformat()
    with _CACHE_LOCK:
        cached = _CACHE.get(today)
        if cached is not None:
            return cached

    _limiter.acquire()
    df = Reference().equity.list_by_exchange()
    df = df[df["exchange"].isin(_ALLOWED)]
    records = df[["exchange", "symbol"]].to_dict(orient="records")
    records.sort(key=lambda r: (r["exchange"], r["symbol"]))
    log.info("Fetched %d symbols for /symbols (HOSE/HNX/UPCOM)", len(records))

    with _CACHE_LOCK:
        _CACHE.clear()
        _CACHE[today] = records
    return records


@router.get("/symbols", response_model=list[SymbolEntry])
async def list_symbols() -> list[SymbolEntry]:
    rows = await asyncio.to_thread(_fetch_symbols)
    return [SymbolEntry(**r) for r in rows]
