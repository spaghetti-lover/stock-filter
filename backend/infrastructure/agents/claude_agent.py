"""Claude implementation using the Claude Agent SDK with FastMCP in-process servers."""

from logger import get_logger

from claude_agent_sdk import query, ClaudeAgentOptions, McpSdkServerConfig, ResultMessage, AssistantMessage, SystemMessage

from domain.agents.agent_provider import AgentProvider
from infrastructure.tools import ToolSet, CHAT_ALL

log = get_logger(__name__)


def _format_history(messages: list[dict]) -> str:
    lines = []
    for m in messages:
        label = "User" if m["role"] == "user" else "Assistant"
        lines.append(f"{label}: {m['content']}")
    return "\n".join(lines)


class ClaudeAgent(AgentProvider):
    def __init__(self, model: str = "claude-sonnet-4-6", toolset: ToolSet = CHAT_ALL):
        self._model = model
        self._mcp_servers = {
            name: McpSdkServerConfig(type="sdk", name=name, instance=server._mcp_server)
            for name, server in toolset.mcp_servers().items()
        }
        self._allowed_tools = toolset.mcp_allowed_tool_ids()

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
