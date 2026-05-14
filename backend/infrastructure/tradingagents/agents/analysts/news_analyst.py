from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import BaseTool

from infrastructure.tradingagents.agents.utils.agent_utils import (
    build_instrument_context,
    get_language_instruction,
)


def create_news_analyst(llm, tools: list[BaseTool]):
    async def news_analyst_node(state):
        current_date = state["trade_date"]
        instrument_context = build_instrument_context(state["company_of_interest"])

        system_message = (
            "You are a news researcher analyzing recent Vietnamese market and macro news. "
            "Write a comprehensive report on current developments that matter for trading the target ticker. "
            "Use the available tools: `stock_news(symbol, limit)` for ticker-specific articles, "
            "`market_news(limit)` for broad market headlines, "
            "`search_news(keyword, limit)` for sector or topic searches (e.g. 'ngân hàng', 'bất động sản'), "
            "and `trending_topics(top_n)` to see what's dominating headlines right now. "
            "Synthesize sentiment, catalysts, regulatory news, and macro signals. Provide actionable insights with citations."
            + """ Append a Markdown table at the end summarizing the key headlines and their implications."""
            + get_language_instruction()
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant, collaborating with other assistants."
                    " Use the provided tools to progress towards answering the question."
                    " If you are unable to fully answer, that's OK; another assistant with different tools"
                    " will help where you left off. Execute what you can to make progress."
                    " If you or any other assistant has the FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** or deliverable,"
                    " prefix your response with FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** so the team knows to stop."
                    " You have access to the following tools: {tool_names}.\n{system_message}"
                    "For your reference, the current date is {current_date}. {instrument_context}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(instrument_context=instrument_context)

        chain = prompt | llm.bind_tools(tools)
        result = await chain.ainvoke(state["messages"])

        report = ""

        if len(result.tool_calls) == 0:
            report = result.content

        return {
            "messages": [result],
            "news_report": report,
        }

    return news_analyst_node
