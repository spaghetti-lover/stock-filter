"""Trading-agent HTTP surface (run + SSE stream + report + catalog)."""

from __future__ import annotations

import asyncio
import json
import os
import re
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from application.dto.trading_agent_dto import (
    AnnouncementsResponse,
    CatalogChoice,
    CatalogResponse,
    DepthOption,
    ProviderOption,
    RunReportResponse,
    RunSnapshotResponse,
    SaveReportRequest,
    SaveReportResponse,
    StartRunRequest,
    StartRunResponse,
)
from application.use_case.trading_agent_use_case import save_report_to_disk, start_run
from infrastructure.tradingagents.runs import attach_loop, detach, get, get_snapshot, stamp_event
from infrastructure.tradingagents.announcements import fetch_announcements
from infrastructure.tradingagents.llm_clients.model_catalog import MODEL_OPTIONS
from infrastructure.tradingagents.models import AnalystType


router = APIRouter(prefix="/trading-agent")


ANALYST_ORDER = [a.value for a in AnalystType]
LANGUAGES = [
    "English", "Chinese", "Japanese", "Korean", "Hindi",
    "Spanish", "Portuguese", "French", "German", "Arabic", "Russian", "Vietnamese",
]
DEPTH_OPTIONS = [
    {"label": "Shallow", "hint": "quick research, few debate rounds", "value": 1},
    {"label": "Medium", "hint": "moderate debate rounds", "value": 3},
    {"label": "Deep", "hint": "comprehensive debate", "value": 5},
]
PROVIDERS = [
    {"label": "OpenAI", "key": "openai", "backend_url": "https://api.openai.com/v1"},
    {"label": "Google", "key": "google", "backend_url": None},
    {"label": "Anthropic", "key": "anthropic", "backend_url": "https://api.anthropic.com/"},
    {"label": "xAI", "key": "xai", "backend_url": "https://api.x.ai/v1"},
    {"label": "DeepSeek", "key": "deepseek", "backend_url": "https://api.deepseek.com"},
    {"label": "Qwen", "key": "qwen", "backend_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"},
    {"label": "GLM", "key": "glm", "backend_url": "https://open.bigmodel.cn/api/paas/v4/"},
    {"label": "OpenRouter", "key": "openrouter", "backend_url": "https://openrouter.ai/api/v1"},
    {"label": "Azure OpenAI", "key": "azure", "backend_url": None},
    {"label": "Ollama", "key": "ollama", "backend_url": "http://localhost:11434/v1"},
]


_RICH_TAG_RE = re.compile(r"\[/?[a-zA-Z][^\[\]]*\]")


def _strip_rich_markup(text: str) -> str:
    return _RICH_TAG_RE.sub("", text)


def _normalize_analysts(raw: list[str]) -> list[str]:
    """Reorder per the canonical analyst ordering and reject empty/unknown selections."""
    seen = {a.lower() for a in raw}
    return [a for a in ANALYST_ORDER if a in seen]


@router.get("/announcements", response_model=AnnouncementsResponse)
async def announcements() -> AnnouncementsResponse:
    data = await asyncio.to_thread(fetch_announcements)
    items = [_strip_rich_markup(line) for line in data.get("announcements", [])]
    return AnnouncementsResponse(
        announcements=[line for line in items if line.strip()],
        require_attention=data.get("require_attention", False),
    )


@router.get("/catalog", response_model=CatalogResponse)
async def catalog() -> CatalogResponse:
    models: dict[str, dict[str, list[CatalogChoice]]] = {}
    for provider, modes in MODEL_OPTIONS.items():
        models[provider] = {
            "quick": [CatalogChoice(label=label, value=value) for label, value in modes.get("quick", [])],
            "deep": [CatalogChoice(label=label, value=value) for label, value in modes.get("deep", [])],
        }
    return CatalogResponse(
        analysts=ANALYST_ORDER,
        languages=LANGUAGES,
        depths=[DepthOption(**d) for d in DEPTH_OPTIONS],
        providers=[ProviderOption(**p) for p in PROVIDERS],
        models=models,
    )


@router.post("/run", response_model=StartRunResponse)
async def run(request: StartRunRequest, fastapi_request: Request) -> StartRunResponse:
    ticker = request.ticker.strip().upper()
    if not ticker:
        raise HTTPException(status_code=400, detail="ticker is empty")

    selected = _normalize_analysts(request.analysts)
    if not selected:
        raise HTTPException(status_code=400, detail="pick at least one analyst")

    if request.research_depth not in (1, 3, 5):
        raise HTTPException(status_code=400, detail="research_depth must be 1, 3 or 5")

    provider_key = request.llm_provider.lower()
    backend_url = request.backend_url
    if backend_url is None:
        backend_url = next((p["backend_url"] for p in PROVIDERS if p["key"] == provider_key), None)

    config = {
        "ticker": ticker,
        "analysis_date": request.analysis_date,
        "output_language": request.output_language or "English",
        "analysts": selected,
        "research_depth": request.research_depth,
        "llm_provider": provider_key,
        "backend_url": backend_url,
        "shallow_thinker": request.shallow_thinker,
        "deep_thinker": request.deep_thinker,
        "google_thinking_level": request.google_thinking_level,
        "openai_reasoning_effort": request.openai_reasoning_effort,
        "anthropic_effort": request.anthropic_effort,
        "checkpoint_enabled": request.checkpoint_enabled,
    }

    tool_registry = fastapi_request.app.state.tool_registry
    run_obj = start_run(config, selected, tool_registry)
    return StartRunResponse(run_id=run_obj.run_id)


@router.get("/stream/{run_id}")
async def stream(run_id: str, request: Request) -> StreamingResponse:
    run_obj = get(run_id)
    if run_obj is None:
        return JSONResponse({"detail": f"run {run_id} not found"}, status_code=404)

    queue = attach_loop(run_obj)

    async def gen():
        snapshot = {
            "type": "snapshot",
            "agents": run_obj.agents,
            "reports": run_obj.reports,
            "stats": run_obj.stats,
            "messages": run_obj.messages[-200:],
            "tool_calls": run_obj.tool_calls[-200:],
            "status": run_obj.status,
        }
        yield _sse_pack(snapshot)

        if run_obj.status in {"done", "error"}:
            yield _sse_pack({"type": "status", "status": run_obj.status, "error": run_obj.error})
            return

        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=20.0)
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
                    continue
                yield _sse_pack(event)
                if event.get("type") == "status" and event.get("status") in {"done", "error"}:
                    break
        finally:
            detach(run_obj)

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/run/{run_id}", response_model=RunSnapshotResponse)
async def run_status(run_id: str) -> RunSnapshotResponse:
    run_obj = get(run_id)
    if run_obj is None:
        raise HTTPException(status_code=404, detail=f"run {run_id} not found")
    return RunSnapshotResponse(**get_snapshot(run_obj))


@router.get("/run/{run_id}/report", response_model=RunReportResponse)
async def run_report(run_id: str) -> RunReportResponse:
    run_obj = get(run_id)
    if run_obj is None:
        raise HTTPException(status_code=404, detail=f"run {run_id} not found")
    return RunReportResponse(
        run_id=run_obj.run_id,
        status=run_obj.status,
        ticker=run_obj.config.get("ticker"),
        analysis_date=run_obj.config.get("analysis_date"),
        reports=run_obj.reports,
        final_state=run_obj.final_state,
    )


@router.post("/run/{run_id}/save", response_model=SaveReportResponse)
async def save_run_report(run_id: str, body: SaveReportRequest) -> SaveReportResponse:
    run_obj = get(run_id)
    if run_obj is None:
        raise HTTPException(status_code=404, detail=f"run {run_id} not found")
    if run_obj.status != "done" or run_obj.final_state is None:
        raise HTTPException(status_code=400, detail="run is not complete")

    save_path = body.save_path or os.path.join(
        os.getcwd(), "reports", f"{run_obj.config['ticker']}_{run_obj.run_id}"
    )

    try:
        report_file = await asyncio.to_thread(save_report_to_disk, run_obj, save_path)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return SaveReportResponse(saved_to=str(report_file.resolve()), save_path=save_path)


def _sse_pack(payload: dict[str, Any]) -> str:
    stamp_event(payload)
    return f"data: {json.dumps(payload, default=str)}\n\n"
