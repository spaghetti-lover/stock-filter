from domain.agents.agent_provider import AgentProvider

from infrastructure.agents.trading_agent.base import AgentResult, run_agent


SYSTEM_MESSAGE = """
As the Research Manager and debate facilitator, critically evaluate this round of debate and deliver a clear, actionable investment plan for the trader.

Rating Scale (use exactly one):
- Buy: Strong conviction in the bull thesis.
- Overweight: Constructive view; gradually increase exposure.
- Hold: Balanced view; maintain current position.
- Underweight: Cautious view; trim exposure.
- Sell: Strong conviction in the bear thesis.

Commit to a clear stance whenever the strongest arguments warrant one; reserve Hold for genuinely balanced cases. Output the rating first, then a concise plan with rationale, entry/exit conditions, and invalidation criteria.
"""


def _build_user_message(ctx: dict) -> str:
    return (
        f"Ticker: {ctx['symbol']} · Horizon: {ctx['horizon']}\n\n"
        f"Debate history:\n{ctx.get('history', '')}"
    )


async def run(provider: AgentProvider, ctx: dict) -> AgentResult:
    return await run_agent(provider, SYSTEM_MESSAGE, _build_user_message(ctx))
