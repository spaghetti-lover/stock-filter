from domain.agents.agent_provider import AgentProvider

from infrastructure.agents.trading_agent.base import AgentResult, run_agent


SYSTEM_MESSAGE = """
You are a news researcher tasked with analyzing recent news and trends over the past week. Please write a comprehensive report of the current state of the world that is relevant for trading and macroeconomics. Use the available news tools: `stock_news` for company-specific articles, `market_news` for general market headlines, `search_news` for keyword/sector queries, and `trending_topics` for the most-discussed phrases of the day. Provide specific, actionable insights with supporting evidence to help traders make informed decisions. Make sure to append a Markdown table at the end of the report to organize key points in the report, organized and easy to read.
"""


async def run(provider: AgentProvider, ctx: dict) -> AgentResult:
    user_message = (
        f"Survey the macro and sector news landscape relevant to ticker {ctx['symbol']} "
        f"(Vietnamese market). Trading horizon: {ctx['horizon']}.\n"
        "Combine company-specific headlines, sector news, and the broader macro backdrop. "
        "Follow the report format described in your system instructions."
    )
    return await run_agent(provider, SYSTEM_MESSAGE, user_message)
