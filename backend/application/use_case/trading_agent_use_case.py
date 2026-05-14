"""Run the TradingAgents graph and stream events to the run queue.

The graph stream is blocking, so the runner executes inside a worker thread and
pushes events via :mod:`infrastructure.tradingagents.runs`.  This module
mirrors the structure of the other use_case files but is graph-aware instead of
repository-driven.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict, Optional

from infrastructure.tradingagents.runs import (
    Run,
    cleanup_old,
    create_run,
    fail_run,
    push_event,
    stamp_event,
)
from infrastructure.tradingagents.cli_helpers import (
    MessageBuffer,
    classify_message_type,
    format_tool_args,
    save_report_to_disk as _save_report_to_disk,
    update_analyst_statuses,
)
from infrastructure.tradingagents.default_config import DEFAULT_CONFIG
from infrastructure.tradingagents.graph.trading_graph import TradingAgentsGraph
from infrastructure.tradingagents.stats_handler import StatsCallbackHandler
from infrastructure.tools import McpToolRegistry


SECTION_TITLE = {
    "market_report": "Market Analysis",
    "sentiment_report": "Social Sentiment",
    "news_report": "News Analysis",
    "fundamentals_report": "Fundamentals Analysis",
    "youtube_report": "YouTube Analysis",
    "investment_plan": "Research Team Decision",
    "trader_investment_plan": "Trading Team Plan",
    "final_trade_decision": "Portfolio Management Decision",
}


def _build_config(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Translate the FE payload (mirrors CLI selections) into a TradingAgents config."""
    cfg = DEFAULT_CONFIG.copy()
    cfg["max_debate_rounds"] = payload["research_depth"]
    cfg["max_risk_discuss_rounds"] = payload["research_depth"]
    cfg["quick_think_llm"] = payload["shallow_thinker"]
    cfg["deep_think_llm"] = payload["deep_thinker"]
    cfg["backend_url"] = payload.get("backend_url")
    cfg["llm_provider"] = payload["llm_provider"].lower()
    cfg["google_thinking_level"] = payload.get("google_thinking_level")
    cfg["openai_reasoning_effort"] = payload.get("openai_reasoning_effort")
    cfg["anthropic_effort"] = payload.get("anthropic_effort")
    cfg["output_language"] = payload.get("output_language", "English")
    cfg["checkpoint_enabled"] = bool(payload.get("checkpoint_enabled", False))
    return cfg


def _emit_agent(run: Run, agent: str, status: str) -> None:
    push_event(run, stamp_event({"type": "agent_status", "agent": agent, "status": status}))


def _emit_report(run: Run, section: str, content: str) -> None:
    push_event(run, stamp_event({
        "type": "report",
        "section": section,
        "title": SECTION_TITLE.get(section, section),
        "content": content,
    }))


def _emit_stats(run: Run, handler: StatsCallbackHandler) -> None:
    push_event(run, stamp_event({"type": "stats", "stats": handler.get_stats()}))


def _emit_message(run: Run, msg_type: str, content: str) -> None:
    push_event(run, stamp_event({"type": "message", "msg_type": msg_type, "content": content}))


def _emit_tool(run: Run, name: str, args: Any) -> None:
    push_event(run, stamp_event({"type": "tool_call", "name": name, "args": format_tool_args(args, 240)}))


def _instrument_buffer(buffer: MessageBuffer, run: Run, handler: StatsCallbackHandler) -> None:
    """Wrap MessageBuffer mutators so every change is emitted to the FE."""
    orig_add_message = buffer.add_message
    orig_add_tool_call = buffer.add_tool_call
    orig_update_status = buffer.update_agent_status
    orig_update_section = buffer.update_report_section

    def add_message(message_type: str, content: Any) -> None:
        orig_add_message(message_type, content)
        _, mtype, body = buffer.messages[-1]
        _emit_message(run, mtype, str(body or ""))
        _emit_stats(run, handler)

    def add_tool_call(name: str, args: Any) -> None:
        orig_add_tool_call(name, args)
        _emit_tool(run, name, args)
        _emit_stats(run, handler)

    def update_agent_status(agent: str, status: str) -> None:
        prev = buffer.agent_status.get(agent)
        orig_update_status(agent, status)
        if buffer.agent_status.get(agent) == status and prev != status:
            _emit_agent(run, agent, status)

    def update_report_section(section: str, content: Any) -> None:
        orig_update_section(section, content)
        new = buffer.report_sections.get(section)
        if new is not None:
            _emit_report(run, section, str(new))

    buffer.add_message = add_message  # type: ignore[assignment]
    buffer.add_tool_call = add_tool_call  # type: ignore[assignment]
    buffer.update_agent_status = update_agent_status  # type: ignore[assignment]
    buffer.update_report_section = update_report_section  # type: ignore[assignment]


def _process_chunk(buffer: MessageBuffer, chunk: Dict[str, Any]) -> None:
    """Mirror cli.main.run_analysis chunk handling without the Rich Live refresh."""
    for message in chunk.get("messages", []):
        msg_id = getattr(message, "id", None)
        if msg_id is not None:
            if msg_id in buffer._processed_message_ids:
                continue
            buffer._processed_message_ids.add(msg_id)

        msg_type, content = classify_message_type(message)
        if content and content.strip():
            buffer.add_message(msg_type, content)

        if hasattr(message, "tool_calls") and message.tool_calls:
            for tc in message.tool_calls:
                if isinstance(tc, dict):
                    buffer.add_tool_call(tc["name"], tc["args"])
                else:
                    buffer.add_tool_call(tc.name, tc.args)

    update_analyst_statuses(buffer, chunk)

    if chunk.get("investment_debate_state"):
        debate = chunk["investment_debate_state"]
        bull = (debate.get("bull_history") or "").strip()
        bear = (debate.get("bear_history") or "").strip()
        judge = (debate.get("judge_decision") or "").strip()
        if bull or bear:
            for a in ("Bull Researcher", "Bear Researcher", "Research Manager"):
                if buffer.agent_status.get(a) == "pending":
                    buffer.update_agent_status(a, "in_progress")
        if bull:
            buffer.update_report_section("investment_plan", f"### Bull Researcher Analysis\n{bull}")
        if bear:
            buffer.update_report_section("investment_plan", f"### Bear Researcher Analysis\n{bear}")
        if judge:
            buffer.update_report_section("investment_plan", f"### Research Manager Decision\n{judge}")
            for a in ("Bull Researcher", "Bear Researcher", "Research Manager"):
                buffer.update_agent_status(a, "completed")
            buffer.update_agent_status("Trader", "in_progress")

    if chunk.get("trader_investment_plan"):
        buffer.update_report_section("trader_investment_plan", chunk["trader_investment_plan"])
        if buffer.agent_status.get("Trader") != "completed":
            buffer.update_agent_status("Trader", "completed")
            buffer.update_agent_status("Aggressive Analyst", "in_progress")

    if chunk.get("risk_debate_state"):
        risk = chunk["risk_debate_state"]
        agg = (risk.get("aggressive_history") or "").strip()
        con = (risk.get("conservative_history") or "").strip()
        neu = (risk.get("neutral_history") or "").strip()
        judge = (risk.get("judge_decision") or "").strip()
        if agg:
            if buffer.agent_status.get("Aggressive Analyst") != "completed":
                buffer.update_agent_status("Aggressive Analyst", "in_progress")
            buffer.update_report_section("final_trade_decision", f"### Aggressive Analyst Analysis\n{agg}")
        if con:
            if buffer.agent_status.get("Conservative Analyst") != "completed":
                buffer.update_agent_status("Conservative Analyst", "in_progress")
            buffer.update_report_section("final_trade_decision", f"### Conservative Analyst Analysis\n{con}")
        if neu:
            if buffer.agent_status.get("Neutral Analyst") != "completed":
                buffer.update_agent_status("Neutral Analyst", "in_progress")
            buffer.update_report_section("final_trade_decision", f"### Neutral Analyst Analysis\n{neu}")
        if judge:
            if buffer.agent_status.get("Portfolio Manager") != "completed":
                buffer.update_agent_status("Portfolio Manager", "in_progress")
                buffer.update_report_section("final_trade_decision", f"### Portfolio Manager Decision\n{judge}")
                for a in (
                    "Aggressive Analyst",
                    "Conservative Analyst",
                    "Neutral Analyst",
                    "Portfolio Manager",
                ):
                    buffer.update_agent_status(a, "completed")


async def _run_pipeline_async(run: Run, tool_registry: McpToolRegistry) -> None:
    """Async worker — build the graph and async-stream chunks into the run queue."""
    cfg = _build_config(run.config)
    handler = StatsCallbackHandler()
    selected = run.selected_analysts

    buffer = MessageBuffer()
    buffer.init_for_analysis(selected)
    _instrument_buffer(buffer, run, handler)

    push_event(run, stamp_event({"type": "status", "status": "running"}))
    push_event(run, stamp_event({"type": "stats", "stats": handler.get_stats()}))

    try:
        graph = TradingAgentsGraph(
            selected,
            config=cfg,
            debug=True,
            callbacks=[handler],
            tool_registry=tool_registry,
        )
    except Exception as exc:
        fail_run(run, exc)
        return

    buffer.add_message("System", f"Selected ticker: {run.config['ticker']}")
    buffer.add_message("System", f"Analysis date: {run.config['analysis_date']}")
    buffer.add_message("System", f"Selected analysts: {', '.join(selected)}")

    first_analyst = f"{selected[0].capitalize()} Analyst"
    buffer.update_agent_status(first_analyst, "in_progress")

    init_state = graph.propagator.create_initial_state(
        run.config["ticker"], run.config["analysis_date"],
        youtube_urls=run.config.get("youtube_urls", []),
    )
    args = graph.propagator.get_graph_args(callbacks=[handler])

    final_state: Optional[Dict[str, Any]] = None
    try:
        async for chunk in graph.graph.astream(init_state, **args):
            _process_chunk(buffer, chunk)
            final_state = chunk
    except Exception as exc:
        fail_run(run, exc)
        return

    for agent in list(buffer.agent_status.keys()):
        buffer.update_agent_status(agent, "completed")
    if final_state is not None:
        for section in list(buffer.report_sections.keys()):
            value = final_state.get(section)
            if value:
                buffer.update_report_section(section, value)

    buffer.add_message("System", f"Completed analysis for {run.config['analysis_date']}")

    if buffer.final_report:
        push_event(run, stamp_event({"type": "complete_report", "content": buffer.final_report}))

    if final_state is not None:
        import json
        compact_final: Dict[str, Any] = {}
        for k, v in final_state.items():
            if k == "messages":
                continue
            try:
                json.dumps(v)
                compact_final[k] = v
            except Exception:
                compact_final[k] = str(v)
        push_event(run, stamp_event({"type": "final_state", "state": compact_final}))

    _emit_stats(run, handler)
    push_event(run, stamp_event({"type": "status", "status": "done"}))


def start_run(
    config: Dict[str, Any],
    selected_analysts: list[str],
    tool_registry: McpToolRegistry,
) -> Run:
    """Create a run and schedule the async pipeline on the running event loop.

    The pipeline MUST share the loop where the FastMCP client sessions were
    opened (the FastAPI main loop, via lifespan). A separate worker-thread loop
    would not see those sessions and tool calls would hang.
    """
    run = create_run(config, selected_analysts)
    run._task = asyncio.create_task(_run_pipeline_async(run, tool_registry))
    cleanup_old()
    return run


def save_report_to_disk(run: Run, save_path: str) -> Path:
    if run.final_state is None:
        raise ValueError("Run has no final state to save")
    return _save_report_to_disk(run.final_state, run.config["ticker"], Path(save_path))
