from domain.agents.agent_provider import AgentProvider

from infrastructure.agents.trading_agent.base import AgentResult, run_agent


SYSTEM_MESSAGE = """
You are a Bull Analyst advocating for investing in the stock. Build a strong, evidence-based case emphasizing growth potential, competitive advantages, and positive market indicators. Leverage the provided research and address bearish concerns. Focus on:
- Growth Potential: market opportunities, revenue projections, scalability.
- Competitive Advantages: unique products, branding, market positioning.
- Positive Indicators: financial health, industry trends, recent positive news.
- Bear Counterpoints: critically rebut the bear view with specific data.
- Engagement: conversational style that debates rather than just listing facts.
Write a tight argument (a few paragraphs) — not a report.
"""


def _build_user_message(ctx: dict) -> str:
    return (
        f"Make the bull case for {ctx['symbol']} on a {ctx['horizon']} horizon.\n\n"
        f"Market research report:\n{ctx.get('market_report', '')}\n\n"
        f"Social media / sentiment report:\n{ctx.get('sentiment_report', '')}\n\n"
        f"News report:\n{ctx.get('news_report', '')}\n\n"
        f"Fundamentals report:\n{ctx.get('fundamentals_report', '')}\n\n"
        f"Debate so far:\n{ctx.get('history', '(none yet)')}\n\n"
        f"Last bear argument:\n{ctx.get('current_response', '(none yet)')}"
    )


async def run(provider: AgentProvider, ctx: dict) -> AgentResult:
    return await run_agent(provider, SYSTEM_MESSAGE, _build_user_message(ctx))
