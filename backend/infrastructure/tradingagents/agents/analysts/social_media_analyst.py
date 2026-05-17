from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import BaseTool

from infrastructure.tradingagents.agents.utils.agent_utils import (
    build_instrument_context,
    get_language_instruction,
)


def create_social_media_analyst(llm, tools: list[BaseTool]):
    async def social_media_analyst_node(state):
        current_date = state["trade_date"]
        instrument_context = build_instrument_context(state["company_of_interest"])

        system_message = (
            "You are a sentiment researcher analyzing Vietnamese retail-investor discussion for a given ticker. "
            "Your corpus is community posts scraped from f319.com (the largest Vietnamese stock forum). "
            "Write a comprehensive report on what retail investors are saying about the company. "
            "Use the available tools: `discussion_by_ticker(symbol, limit, days)` for posts tagged with the ticker, and "
            "`discussion_search(keyword, limit, days)` to dig into related themes, company aliases, sector reactions, "
            "or rumor/news terms (e.g. 'cổ tức', 'chia thưởng', the company short name). "
            "Look across many posts, surface positive/negative sentiment, recurring concerns, emerging narratives, "
            "and notable retail-investor claims (with explicit caution that forum posts are unverified). "
            "Quote post excerpts and include their URLs."
            + """ Append a Markdown table at the end summarizing sentiment by topic."""
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
            "sentiment_report": report,
        }

    return social_media_analyst_node
