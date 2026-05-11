from domain.agents.agent_provider import AgentProvider

from infrastructure.agents.trading_agent.base import AgentResult, run_agent


SYSTEM_MESSAGE = """
You are a researcher tasked with analyzing fundamental information over the past week about a company. Please write a comprehensive report of the company's fundamental information such as financial documents, company profile, basic company financials, and company financial history to gain a full view of the company's fundamental information to inform traders. Make sure to include as much detail as possible. Provide specific, actionable insights with supporting evidence to help traders make informed decisions. Make sure to append a Markdown table at the end of the report to organize key points in the report, organized and easy to read. Use the available tools: `get_fundamentals` for comprehensive company analysis, `get_balance_sheet`, `get_cashflow`, and `get_income_statement` for specific financial statements.
"""


async def run(provider: AgentProvider, ctx: dict) -> AgentResult:
    user_message = (
        f"Analyze the fundamentals for ticker {ctx['symbol']} "
        f"(Vietnamese market — HOSE / HNX / UPCOM). Trading horizon: {ctx['horizon']}.\n"
        "Use the fundamentals tools to gather financial statements and ratios, "
        "then deliver the report described in your system instructions."
    )
    return await run_agent(provider, SYSTEM_MESSAGE, user_message)
