from domain.agents.agent_provider import AgentProvider

from infrastructure.agents.trading_agent.base import AgentResult, run_agent


SYSTEM_MESSAGE = """
You are a social media and company-specific news researcher tasked with analyzing public sentiment for a specific company over the past week. Your objective is to write a comprehensive report detailing your analysis, insights, and implications for traders on this company's current state based on what people are saying. Use `stock_news`, `search_news`, and `trending_topics` to gather company-related discussions and sentiment signals. Provide specific, actionable insights with supporting evidence to help traders make informed decisions. Make sure to append a Markdown table at the end of the report to organize key points in the report, organized and easy to read.
"""


async def run(provider: AgentProvider, ctx: dict) -> AgentResult:
    user_message = (
        f"Gauge the public sentiment and discussion intensity around ticker {ctx['symbol']} "
        f"(Vietnamese market). Trading horizon: {ctx['horizon']}.\n"
        "Search for company-specific chatter, retail interest signals, and sentiment polarity. "
        "Follow the report format described in your system instructions."
    )
    return await run_agent(provider, SYSTEM_MESSAGE, user_message)
