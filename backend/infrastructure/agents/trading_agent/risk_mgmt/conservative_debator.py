from domain.agents.agent_provider import AgentProvider

from infrastructure.agents.trading_agent.base import AgentResult, run_agent


SYSTEM_MESSAGE = """
You are the Conservative Risk Analyst. Prioritize capital preservation, stability, and risk mitigation. When evaluating the trader's decision, critically examine high-risk elements and point out where caution would secure long-term gains. Use the supplied reports to counter the aggressive and neutral views. Be conversational; debate, don't list. Keep the argument tight (a few paragraphs).
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
        f"Last neutral argument:\n{ctx.get('current_neutral_response', '(none yet)')}"
    )


async def run(provider: AgentProvider, ctx: dict) -> AgentResult:
    return await run_agent(provider, SYSTEM_MESSAGE, _build_user_message(ctx))
