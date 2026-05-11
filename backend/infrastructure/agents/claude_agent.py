"""Claude implementation using the Claude Agent SDK with a FastMCP in-process server."""

from logger import get_logger

from claude_agent_sdk import query, ClaudeAgentOptions, McpSdkServerConfig, ResultMessage, AssistantMessage, SystemMessage

from domain.agents.agent_provider import AgentProvider
from infrastructure.agents.stock_tools import mcp

log = get_logger(__name__)

_SERVER_NAME = "stock-data"

TOOL_NAMES = [
    f"mcp__{_SERVER_NAME}__list_symbols",
    f"mcp__{_SERVER_NAME}__trading_history",
    f"mcp__{_SERVER_NAME}__intraday_data",
    f"mcp__{_SERVER_NAME}__stock_price",
    f"mcp__{_SERVER_NAME}__compare_stocks",
    f"mcp__{_SERVER_NAME}__stock_news",
    f"mcp__{_SERVER_NAME}__market_news",
    f"mcp__{_SERVER_NAME}__search_news",
    f"mcp__{_SERVER_NAME}__trending_topics",
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
        self._mcp_server = McpSdkServerConfig(
            type="sdk",
            name=_SERVER_NAME,
            instance=mcp._mcp_server,
        )

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
                mcp_servers={_SERVER_NAME: self._mcp_server},
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
