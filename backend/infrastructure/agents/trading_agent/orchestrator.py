"""4-phase orchestration: analysts → research debate → trader → risk debate."""

from __future__ import annotations

import asyncio
import re
from typing import Awaitable, Callable

from infrastructure.agents.factory import get_agent_provider
from infrastructure.agents.mcp_config import (
    DATA_ONLY,
    FUNDAMENTALS_ONLY,
    McpConfig,
    NEWS_ONLY,
)
from infrastructure.agents.trading_agent.analysts import (
    fundamentals_analyst,
    market_analyst,
    news_analyst,
    social_media_analyst,
)
from infrastructure.agents.trading_agent.managers import (
    portfolio_manager,
    research_manager,
)
from infrastructure.agents.trading_agent.researchers import bear_researcher, bull_researcher
from infrastructure.agents.trading_agent.risk_mgmt import (
    aggressive_debator,
    conservative_debator,
    neutral_debator,
)
from infrastructure.agents.trading_agent.trader import trader

UpdateCallback = Callable[[str, dict], Awaitable[None] | None]

_NO_TOOLS = McpConfig(servers=[], allowed_tools=[])

_RATING_TO_ACTION = {
    "buy": "BUY",
    "overweight": "BUY",
    "hold": "HOLD",
    "underweight": "SELL",
    "sell": "SELL",
}


def _parse_verdict(portfolio_text: str, trader_text: str) -> dict:
    action = "HOLD"
    rating_match = re.search(r"RATING:\s*(buy|overweight|hold|underweight|sell)", portfolio_text, re.I)
    if rating_match:
        action = _RATING_TO_ACTION[rating_match.group(1).lower()]
    else:
        for word, mapped in _RATING_TO_ACTION.items():
            if re.search(rf"\b{word}\b", portfolio_text, re.I):
                action = mapped
                break

    target = _extract(trader_text, r"target[^\n]*?([+\-]?\d+(?:\.\d+)?%)")
    stop = _extract(trader_text, r"stop[^\n]*?(-?\d+(?:\.\d+)?%)")
    size = _extract(trader_text, r"size[^\n]*?(\d+(?:\.\d+)?%)") or _extract(
        trader_text, r"(\d+(?:\.\d+)?%\s*of\s*NAV)"
    )

    return {
        "action": action,
        "confidence": 0.7 if rating_match else 0.55,
        "target": target or "—",
        "stop": stop or "—",
        "size": size or "—",
        "rationale": portfolio_text.strip() or "(no rationale)",
    }


def _extract(text: str, pattern: str) -> str | None:
    match = re.search(pattern, text, re.I)
    return match.group(1) if match else None


class TradingPipeline:
    def __init__(self, provider_name: str, on_update: UpdateCallback):
        self._provider_name = provider_name
        self._on_update = on_update

    async def _emit(self, key: str, patch: dict) -> None:
        result = self._on_update(key, patch)
        if asyncio.iscoroutine(result):
            await result

    def _provider(self, mcp_config: McpConfig):
        return get_agent_provider(self._provider_name, mcp_config=mcp_config)

    async def _run_step(self, key: str, mcp_config: McpConfig, runner, ctx: dict) -> str:
        await self._emit(key, {"status": "running"})
        try:
            result = await runner(self._provider(mcp_config), ctx)
        except Exception as exc:  # surface failure to the FE
            await self._emit(key, {"status": "error", "error": str(exc)})
            raise
        await self._emit(
            key,
            {"status": "done", "report": result.report, "duration": result.duration},
        )
        return result.report

    async def run(self, symbol: str, horizon: str) -> dict:
        base_ctx = {"symbol": symbol, "horizon": horizon}

        # Phase 1 — analysts in parallel
        fundamental_task = asyncio.create_task(
            self._run_step("fundamental", FUNDAMENTALS_ONLY, fundamentals_analyst.run, base_ctx)
        )
        technical_task = asyncio.create_task(
            self._run_step("technical", DATA_ONLY, market_analyst.run, base_ctx)
        )
        news_task = asyncio.create_task(
            self._run_step("news", NEWS_ONLY, news_analyst.run, base_ctx)
        )
        sentiment_task = asyncio.create_task(
            self._run_step("sentiment", NEWS_ONLY, social_media_analyst.run, base_ctx)
        )
        fundamentals_report, market_report, news_report, sentiment_report = await asyncio.gather(
            fundamental_task, technical_task, news_task, sentiment_task
        )

        research_ctx = {
            **base_ctx,
            "market_report": market_report,
            "sentiment_report": sentiment_report,
            "news_report": news_report,
            "fundamentals_report": fundamentals_report,
            "history": "",
            "current_response": "",
        }

        # Phase 2 — bull → bear → research manager (one round)
        bull_text = await self._run_step("bull", _NO_TOOLS, bull_researcher.run, research_ctx)
        bear_ctx = {**research_ctx, "current_response": bull_text}
        bear_text = await self._run_step("bear", _NO_TOOLS, bear_researcher.run, bear_ctx)

        debate_history = (
            f"Bull:\n{bull_text}\n\nBear:\n{bear_text}"
        )
        manager_ctx = {**base_ctx, "history": debate_history}
        research_plan = await self._run_step(
            "research_manager", _NO_TOOLS, research_manager.run, manager_ctx
        )

        # Phase 3 — trader
        trader_ctx = {**base_ctx, "investment_plan": research_plan}
        trader_plan = await self._run_step("trader", _NO_TOOLS, trader.run, trader_ctx)

        # Phase 4 — risk debaters → portfolio manager
        risk_ctx_base = {
            **base_ctx,
            "trader_decision": trader_plan,
            "market_report": market_report,
            "sentiment_report": sentiment_report,
            "news_report": news_report,
            "fundamentals_report": fundamentals_report,
            "history": "",
            "current_aggressive_response": "",
            "current_conservative_response": "",
            "current_neutral_response": "",
        }
        aggressive_text = await self._run_step(
            "aggressive", _NO_TOOLS, aggressive_debator.run, risk_ctx_base
        )
        conservative_ctx = {**risk_ctx_base, "current_aggressive_response": aggressive_text}
        conservative_text = await self._run_step(
            "conservative", _NO_TOOLS, conservative_debator.run, conservative_ctx
        )
        neutral_ctx = {
            **risk_ctx_base,
            "current_aggressive_response": aggressive_text,
            "current_conservative_response": conservative_text,
        }
        neutral_text = await self._run_step(
            "neutral", _NO_TOOLS, neutral_debator.run, neutral_ctx
        )

        risk_history = (
            f"Aggressive:\n{aggressive_text}\n\n"
            f"Conservative:\n{conservative_text}\n\n"
            f"Neutral:\n{neutral_text}"
        )
        pm_ctx = {
            **base_ctx,
            "research_plan": research_plan,
            "trader_plan": trader_plan,
            "history": risk_history,
        }
        pm_text = await self._run_step(
            "portfolio_manager", _NO_TOOLS, portfolio_manager.run, pm_ctx
        )

        verdict = _parse_verdict(pm_text, trader_plan)
        verdict["horizon"] = horizon
        return verdict
