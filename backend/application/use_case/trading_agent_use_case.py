"""Trading-agent run registry + executor.

Runs are kept in a process-local dict — FastAPI polls them via the status route.
Not durable across restarts; persistence can be added later.
"""

from __future__ import annotations

import asyncio
import time
import uuid

from logger import get_logger

from infrastructure.agents.trading_agent.orchestrator import TradingPipeline

log = get_logger(__name__)

_RUNS: dict[str, dict] = {}

_AGENT_KEYS = [
    "fundamental", "technical", "news", "sentiment",
    "bull", "bear", "research_manager",
    "trader",
    "aggressive", "conservative", "neutral", "portfolio_manager",
]


def _new_run_state(symbol: str, horizon: str) -> dict:
    return {
        "run_id": "",
        "symbol": symbol,
        "horizon": horizon,
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "running",
        "agents": {k: {"status": "pending"} for k in _AGENT_KEYS},
        "verdict": None,
        "error": None,
    }


def start_run(symbol: str, horizon: str, provider: str) -> str:
    run_id = uuid.uuid4().hex[:12]
    state = _new_run_state(symbol, horizon)
    state["run_id"] = run_id
    _RUNS[run_id] = state

    def on_update(key: str, patch: dict) -> None:
        agent_state = _RUNS[run_id]["agents"].setdefault(key, {"status": "pending"})
        agent_state.update(patch)

    pipeline = TradingPipeline(provider_name=provider, on_update=on_update)

    async def _execute() -> None:
        try:
            verdict = await pipeline.run(symbol, horizon)
            _RUNS[run_id]["verdict"] = verdict
            _RUNS[run_id]["status"] = "done"
        except Exception as exc:
            log.exception("Trading-agent run %s failed", run_id)
            _RUNS[run_id]["status"] = "error"
            _RUNS[run_id]["error"] = str(exc)

    asyncio.create_task(_execute())
    return run_id


def get_run(run_id: str) -> dict | None:
    return _RUNS.get(run_id)
