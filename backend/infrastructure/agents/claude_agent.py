"""Claude implementation using the Claude Agent SDK with FastMCP in-process servers."""

from logger import get_logger

from claude_agent_sdk import query, ClaudeAgentOptions, McpSdkServerConfig, ResultMessage, AssistantMessage, SystemMessage

from domain.agents.agent_provider import AgentProvider
from infrastructure.agents.mcp_config import McpConfig, ALL_TOOLS
from infrastructure.mcp.data import mcp as data_mcp
from infrastructure.mcp.news import mcp as news_mcp
from infrastructure.mcp.fundamentals import mcp as fundamentals_mcp

log = get_logger(__name__)

_MCP_SERVER_MAP = {
    "data":         lambda: McpSdkServerConfig(type="sdk", name="data",         instance=data_mcp._mcp_server),
    "news":         lambda: McpSdkServerConfig(type="sdk", name="news",         instance=news_mcp._mcp_server),
    "fundamentals": lambda: McpSdkServerConfig(type="sdk", name="fundamentals", instance=fundamentals_mcp._mcp_server),
}


def _format_history(messages: list[dict]) -> str:
    lines = []
    for m in messages:
        label = "User" if m["role"] == "user" else "Assistant"
        lines.append(f"{label}: {m['content']}")
    return "\n".join(lines)


class ClaudeAgent(AgentProvider):
    def __init__(self, model: str = "claude-sonnet-4-6", mcp_config: McpConfig = ALL_TOOLS):
        self._model = model
        self._mcp_servers = {name: _MCP_SERVER_MAP[name]() for name in mcp_config.servers}
        self._allowed_tools = mcp_config.allowed_tools

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
                mcp_servers=self._mcp_servers, # pyright: ignore[reportArgumentType]
                allowed_tools=self._allowed_tools,
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
