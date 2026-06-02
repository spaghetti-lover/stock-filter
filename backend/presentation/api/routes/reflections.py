"""Read-only endpoint exposing past reflection entries from the trading memory log.

Powers the Stock Copilot reflection sidebar — examiners can see how the system
accumulates lessons across runs for a given ticker.
"""

from fastapi import APIRouter

from infrastructure.tradingagents.agents.utils.memory import TradingMemoryLog
from infrastructure.tradingagents.default_config import DEFAULT_CONFIG

router = APIRouter(prefix="/reflections", tags=["reflections"])


@router.get("/{ticker}")
async def get_reflections(ticker: str, limit: int = 5) -> dict:
    """Return up to `limit` resolved reflection entries for `ticker`, newest-first."""
    ticker = ticker.upper()
    memory = TradingMemoryLog(DEFAULT_CONFIG)
    entries = [
        e for e in memory.load_entries()
        if not e.get("pending") and e["ticker"] == ticker and e.get("reflection")
    ]
    entries.reverse()
    return {
        "ticker": ticker,
        "count": len(entries[:limit]),
        "entries": [
            {
                "date": e["date"],
                "rating": e["rating"],
                "raw": e.get("raw"),
                "alpha": e.get("alpha"),
                "holding": e.get("holding"),
                "reflection": e["reflection"],
            }
            for e in entries[:limit]
        ],
    }
