from domain.agents.agent_provider import AgentProvider

from infrastructure.agents.trading_agent.base import AgentResult, run_agent


SYSTEM_MESSAGE = """
You are a Bear Analyst making the case against investing in the stock. Present a well-reasoned argument emphasizing risks, challenges, and negative indicators. Focus on:
- Risks and Challenges: market saturation, financial instability, macro threats.
- Competitive Weaknesses: weak positioning, declining innovation, competitor threats.
- Negative Indicators: adverse financials, market trends, recent bad news.
- Bull Counterpoints: critically rebut the bull view with specific data.
- Engagement: conversational style that debates rather than just listing facts.
Write a tight argument (a few paragraphs) — not a report.
"""


def _build_user_message(ctx: dict) -> str:
    return (
        f"Make the bear case against {ctx['symbol']} on a {ctx['horizon']} horizon.\n\n"
        f"Market research report:\n{ctx.get('market_report', '')}\n\n"
        f"Social media / sentiment report:\n{ctx.get('sentiment_report', '')}\n\n"
        f"News report:\n{ctx.get('news_report', '')}\n\n"
        f"Fundamentals report:\n{ctx.get('fundamentals_report', '')}\n\n"
        f"Debate so far:\n{ctx.get('history', '(none yet)')}\n\n"
        f"Last bull argument:\n{ctx.get('current_response', '(none yet)')}"
    )


async def run(provider: AgentProvider, ctx: dict) -> AgentResult:
    return await run_agent(provider, SYSTEM_MESSAGE, _build_user_message(ctx))
