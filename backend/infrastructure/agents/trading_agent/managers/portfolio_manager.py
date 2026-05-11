from domain.agents.agent_provider import AgentProvider

from infrastructure.agents.trading_agent.base import AgentResult, run_agent


SYSTEM_MESSAGE = """
As the Portfolio Manager, synthesize the risk analysts' debate and deliver the final trading decision.

Rating Scale (use exactly one — place it on the first line as `RATING: <one of>`):
- Buy: Strong conviction to enter or add to position.
- Overweight: Favorable outlook, gradually increase exposure.
- Hold: Maintain current position, no action needed.
- Underweight: Reduce exposure, take partial profits.
- Sell: Exit position or avoid entry.

Be decisive and ground every conclusion in evidence from the analysts and the trader's plan. After the rating, write a concise rationale (a few short paragraphs) covering the deciding factors, position sizing, and invalidation conditions.
"""


def _build_user_message(ctx: dict) -> str:
    return (
        f"Ticker: {ctx['symbol']} · Horizon: {ctx['horizon']}\n\n"
        f"Research manager's investment plan:\n{ctx.get('research_plan', '')}\n\n"
        f"Trader's transaction proposal:\n{ctx.get('trader_plan', '')}\n\n"
        f"Risk analysts debate history:\n{ctx.get('history', '')}"
    )


async def run(provider: AgentProvider, ctx: dict) -> AgentResult:
    return await run_agent(provider, SYSTEM_MESSAGE, _build_user_message(ctx))
