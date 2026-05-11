"""Claude implementation using the Claude Agent SDK with FastMCP in-process servers."""

from logger import get_logger

from claude_agent_sdk import query, ClaudeAgentOptions, McpSdkServerConfig, ResultMessage, AssistantMessage, SystemMessage

from domain.agents.agent_provider import AgentProvider
from infrastructure.mcp.data import mcp as data_mcp
from infrastructure.mcp.news import mcp as news_mcp
from infrastructure.mcp.fundamentals import mcp as fundamentals_mcp

log = get_logger(__name__)

TOOL_NAMES = [
    "mcp__data__list_symbols",
    "mcp__data__trading_history",
    "mcp__data__intraday_data",
    "mcp__data__stock_price",
    "mcp__data__compare_stocks",
    "mcp__news__stock_news",
    "mcp__news__market_news",
    "mcp__news__search_news",
    "mcp__news__trending_topics",
    "mcp__fundamentals__get_fundamentals",
    "mcp__fundamentals__get_balance_sheet",
    "mcp__fundamentals__get_cashflow",
    "mcp__fundamentals__get_income_statement",
]


def _format_history(messages: list[dict]) -> str:
    lines = []
    for m in messages:
        label = "User" if m["role"] == "user" else "Assistant"
        lines.append(f"{label}: {m['content']}")
    return "\n".join(lines)


class ClaudeAgent(AgentProvider):
    def __init__(self, model: str = "claude-sonnet-4-6"):
        self._model = model
        self._mcp_servers = {
            "data": McpSdkServerConfig(type="sdk", name="data", instance=data_mcp._mcp_server),
            "news": McpSdkServerConfig(type="sdk", name="news", instance=news_mcp._mcp_server),
            "fundamentals": McpSdkServerConfig(type="sdk", name="fundamentals", instance=fundamentals_mcp._mcp_server),
        }

    async def chat(self, messages: list[dict], system_prompt: str) -> str:
        if len(messages) > 1:
            history = _format_history(messages[:-1])
            prompt = f"Conversation so far:\n{history}\n\nUser: {messages[-1]['content']}"
        else:
            prompt = messages[-1]["content"]

        async for message in query(
            prompt=prompt,
            options=ClaudeAgentOptions(
                model=self._model,
                system_prompt=system_prompt,
                mcp_servers=self._mcp_servers,
                allowed_tools=TOOL_NAMES,
            ),
        ):
            if isinstance(message, ResultMessage):
                if message.is_error:
                    return f"Error: {message.result or 'unknown error'}"
                return message.result or ""
            elif isinstance(message, AssistantMessage):
                log.info(f"Assistant message: {message}")
            elif isinstance(message, SystemMessage):
                log.info(f"System message: {message.data}")
        return ""
