from domain.agents.agent_provider import AgentProvider

from infrastructure.agents.trading_agent.base import AgentResult, run_agent


SYSTEM_MESSAGE = """
You are a trading agent translating an investment plan into a concrete transaction proposal. Anchor your reasoning in the analysts' reports and the research manager's plan. Output:
- Action: BUY, SELL, or HOLD (start the response with `FINAL TRANSACTION PROPOSAL: **BUY/SELL/HOLD**`).
- Size (as a % of NAV).
- Entry conditions / timing.
- Target (% gain or price).
- Stop loss (% loss or price).
- One paragraph of rationale tying back to the analysts and plan.
"""


def _build_user_message(ctx: dict) -> str:
    return (
        f"Ticker: {ctx['symbol']} · Horizon: {ctx['horizon']}\n\n"
        f"Investment plan from the research manager:\n{ctx.get('investment_plan', '')}\n\n"
        "Use this plan as the foundation for your transaction proposal."
    )


async def run(provider: AgentProvider, ctx: dict) -> AgentResult:
    return await run_agent(provider, SYSTEM_MESSAGE, _build_user_message(ctx))
