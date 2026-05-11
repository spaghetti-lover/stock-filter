"""Shared helpers for trading-agent pipeline agents."""

from __future__ import annotations

import time
from dataclasses import dataclass

from domain.agents.agent_provider import AgentProvider


@dataclass
class AgentResult:
    report: str
    duration: float


async def run_agent(
    provider: AgentProvider,
    system_prompt: str,
    user_message: str,
) -> AgentResult:
    started = time.perf_counter()
    report = await provider.chat(
        messages=[{"role": "user", "content": user_message}],
        system_prompt=system_prompt,
    )
    return AgentResult(report=report, duration=time.perf_counter() - started)
