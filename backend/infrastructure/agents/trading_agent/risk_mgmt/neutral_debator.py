from domain.agents.agent_provider import AgentProvider

from infrastructure.agents.trading_agent.base import AgentResult, run_agent


SYSTEM_MESSAGE = """
You are the Neutral Risk Analyst. Weigh both upside and downside, factor in broader market trends and diversification. Challenge both the aggressive and conservative views where each may be overly optimistic or overly cautious, and advocate for a balanced, sustainable strategy. Be conversational; debate, don't list. Keep the argument tight (a few paragraphs).
"""


def _build_user_message(ctx: dict) -> str:
    return (
        f"Trader's transaction proposal:\n{ctx.get('trader_decision', '')}\n\n"
        f"Market research report:\n{ctx.get('market_report', '')}\n\n"
        f"Sentiment report:\n{ctx.get('sentiment_report', '')}\n\n"
        f"News report:\n{ctx.get('news_report', '')}\n\n"
        f"Fundamentals report:\n{ctx.get('fundamentals_report', '')}\n\n"
        f"Debate so far:\n{ctx.get('history', '(none yet)')}\n\n"
        f"Last aggressive argument:\n{ctx.get('current_aggressive_response', '(none yet)')}\n\n"
        f"Last conservative argument:\n{ctx.get('current_conservative_response', '(none yet)')}"
    )


async def run(provider: AgentProvider, ctx: dict) -> AgentResult:
    return await run_agent(provider, SYSTEM_MESSAGE, _build_user_message(ctx))
