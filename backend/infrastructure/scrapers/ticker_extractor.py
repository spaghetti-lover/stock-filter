import re

from db.connection import get_pool
from logger import get_logger

log = get_logger(__name__)

_TICKER_RE = re.compile(r"\b([A-Z]{3})\b")
_WHITELIST: set[str] | None = None


async def load_whitelist() -> set[str]:
    global _WHITELIST
    if _WHITELIST is not None:
        return _WHITELIST
    pool = get_pool()
    rows = await pool.fetch("SELECT symbol FROM stock_metrics")
    _WHITELIST = {r["symbol"].upper() for r in rows if r["symbol"]}
    log.info("Ticker whitelist loaded: %d symbols", len(_WHITELIST))
    return _WHITELIST


def invalidate_whitelist() -> None:
    global _WHITELIST
    _WHITELIST = None


def extract_tickers(text: str) -> tuple[str, ...]:
    if _WHITELIST is None or not text:
        return ()
    seen: set[str] = set()
    out: list[str] = []
    for m in _TICKER_RE.finditer(text):
        sym = m.group(1)
        if sym in _WHITELIST and sym not in seen:
            seen.add(sym)
            out.append(sym)
    return tuple(out)
