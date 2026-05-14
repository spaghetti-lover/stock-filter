from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import BaseTool

from infrastructure.tradingagents.agents.utils.agent_utils import (
    build_instrument_context,
    get_language_instruction,
)


def create_youtube_analyst(llm, tools: list[BaseTool]):
    async def youtube_analyst_node(state):
        current_date = state["trade_date"]
        instrument_context = build_instrument_context(state["company_of_interest"])
        youtube_urls = state.get("youtube_urls") or []

        if not youtube_urls:
            return {
                "messages": [],
                "youtube_report": "No YouTube URLs were provided. Skipping YouTube video analysis.",
            }

        urls_block = "\n".join(f"- {u}" for u in youtube_urls)

        system_message = (
            "You are a YouTube video analyst specializing in Vietnamese stock and financial content. "
            "The user has provided the following YouTube video URLs for analysis:\n"
            f"{urls_block}\n\n"
            "For each URL, call `get_youtube_transcript(url)` to retrieve the full transcript. "
            "After fetching all transcripts, analyze their content in the context of the target stock symbol. "
            "Look for: analyst opinions, company news or announcements, CEO statements, investor sentiment, "
            "sector trends, and any forward-looking commentary relevant to the ticker. "
            "Synthesize the insights across all videos into a coherent report. "
            "If a transcript is unavailable (tool returns an error), note it and continue with the others. "
            "Provide specific quotes from the transcripts where relevant."
            + " Append a Markdown table summarizing the key insights per video URL."
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
            "youtube_report": report,
        }

    return youtube_analyst_node
