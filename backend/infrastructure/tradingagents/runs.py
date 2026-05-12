"""In-process registry of trading-agent runs.

A run is started by the API; the LangGraph stream is blocking so it runs on a
background worker thread. Progress events land in a per-run asyncio queue that
the SSE endpoint drains. The registry also caches the rendered state so the FE
can fetch a snapshot/report after the stream closes.
"""

from __future__ import annotations

import asyncio
import datetime
import threading
import time
import traceback
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


EventDict = Dict[str, Any]


_ANALYST_AGENT_NAMES = {
    "market": "Market Analyst",
    "social": "Social Analyst",
    "news": "News Analyst",
    "fundamentals": "Fundamentals Analyst",
}
_FIXED_TEAMS = {
    "Research Team": ["Bull Researcher", "Bear Researcher", "Research Manager"],
    "Trading Team": ["Trader"],
    "Risk Management": ["Aggressive Analyst", "Neutral Analyst", "Conservative Analyst"],
    "Portfolio Management": ["Portfolio Manager"],
}
_REPORT_SECTIONS = [
    "market_report",
    "sentiment_report",
    "news_report",
    "fundamentals_report",
    "investment_plan",
    "trader_investment_plan",
    "final_trade_decision",
]
_REPORT_SECTION_ANALYST = {
    "market_report": "market",
    "sentiment_report": "social",
    "news_report": "news",
    "fundamentals_report": "fundamentals",
}


@dataclass
class Run:
    run_id: str
    config: Dict[str, Any]
    selected_analysts: List[str]
    started_at: float
    status: str = "pending"  # pending | running | done | error
    error: Optional[str] = None
    final_state: Optional[Dict[str, Any]] = None

    agents: Dict[str, str] = field(default_factory=dict)
    reports: Dict[str, str] = field(default_factory=dict)
    messages: List[Dict[str, str]] = field(default_factory=list)
    tool_calls: List[Dict[str, str]] = field(default_factory=list)
    stats: Dict[str, int] = field(default_factory=lambda: {
        "llm_calls": 0,
        "tool_calls": 0,
        "tokens_in": 0,
        "tokens_out": 0,
    })

    _queue: Optional[asyncio.Queue] = None
    _loop: Optional[asyncio.AbstractEventLoop] = None
    _thread: Optional[threading.Thread] = None
    _subscribers: int = 0


_RUNS: Dict[str, Run] = {}
_LOCK = threading.Lock()


def _init_agents(selected: List[str]) -> Dict[str, str]:
    agents: Dict[str, str] = {}
    for key in selected:
        if key in _ANALYST_AGENT_NAMES:
            agents[_ANALYST_AGENT_NAMES[key]] = "pending"
    for members in _FIXED_TEAMS.values():
        for agent in members:
            agents[agent] = "pending"
    return agents


def _init_reports(selected: List[str]) -> List[str]:
    out: List[str] = []
    for section in _REPORT_SECTIONS:
        analyst = _REPORT_SECTION_ANALYST.get(section)
        if analyst is None or analyst in selected:
            out.append(section)
    return out


def create_run(config: Dict[str, Any], selected_analysts: List[str]) -> Run:
    run_id = uuid.uuid4().hex[:12]
    run = Run(
        run_id=run_id,
        config=config,
        selected_analysts=selected_analysts,
        started_at=time.time(),
        agents=_init_agents(selected_analysts),
        reports={s: "" for s in _init_reports(selected_analysts)},
    )
    with _LOCK:
        _RUNS[run_id] = run
    return run


def get(run_id: str) -> Optional[Run]:
    return _RUNS.get(run_id)


def attach_loop(run: Run) -> asyncio.Queue:
    """Bind the run to the current asyncio loop and return its event queue.

    Called from the SSE endpoint right before consumption; the background worker
    pushes events with ``loop.call_soon_threadsafe``.
    """
    if run._queue is None:
        run._queue = asyncio.Queue()
        run._loop = asyncio.get_running_loop()
    run._subscribers += 1
    return run._queue


def detach(run: Run) -> None:
    run._subscribers = max(0, run._subscribers - 1)


def push_event(run: Run, event: EventDict) -> None:
    """Thread-safe push that updates the cached snapshot fields too."""
    et = event.get("type")
    if et == "agent_status":
        run.agents[event["agent"]] = event["status"]
    elif et == "report":
        run.reports[event["section"]] = event["content"]
    elif et == "message":
        run.messages.append({
            "time": event["time"],
            "type": event["msg_type"],
            "content": event["content"],
        })
        if len(run.messages) > 400:
            run.messages = run.messages[-400:]
    elif et == "tool_call":
        run.tool_calls.append({
            "time": event["time"],
            "name": event["name"],
            "args": event["args"],
        })
        if len(run.tool_calls) > 400:
            run.tool_calls = run.tool_calls[-400:]
    elif et == "stats":
        run.stats = event["stats"]
    elif et == "status":
        run.status = event["status"]
        if event.get("error"):
            run.error = event["error"]
    elif et == "final_state":
        run.final_state = event["state"]

    queue = run._queue
    loop = run._loop
    if queue is not None and loop is not None:
        loop.call_soon_threadsafe(queue.put_nowait, event)


def stamp_event(payload: EventDict) -> EventDict:
    payload.setdefault("time", datetime.datetime.now().strftime("%H:%M:%S"))
    return payload


def fail_run(run: Run, exc: BaseException) -> None:
    tb = traceback.format_exc()
    run.status = "error"
    run.error = f"{type(exc).__name__}: {exc}"
    push_event(run, stamp_event({
        "type": "status",
        "status": "error",
        "error": run.error,
        "traceback": tb,
    }))


def get_snapshot(run: Run) -> Dict[str, Any]:
    elapsed = int(time.time() - run.started_at)
    return {
        "run_id": run.run_id,
        "status": run.status,
        "started_at": datetime.datetime.fromtimestamp(run.started_at).isoformat(timespec="seconds"),
        "elapsed_seconds": elapsed,
        "config": run.config,
        "selected_analysts": run.selected_analysts,
        "agents": run.agents,
        "reports": run.reports,
        "messages": run.messages[-200:],
        "tool_calls": run.tool_calls[-200:],
        "stats": run.stats,
        "error": run.error,
        "has_final_state": run.final_state is not None,
    }


def cleanup_old(max_age_seconds: int = 60 * 60 * 6) -> None:
    """Drop terminal runs older than ``max_age_seconds`` with no live subscribers."""
    now = time.time()
    with _LOCK:
        for rid in list(_RUNS.keys()):
            r = _RUNS[rid]
            if r._subscribers > 0:
                continue
            if r.status in {"done", "error"} and now - r.started_at > max_age_seconds:
                _RUNS.pop(rid, None)
