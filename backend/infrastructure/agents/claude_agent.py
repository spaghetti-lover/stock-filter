"""Claude implementation using the Claude Agent SDK (claude-agent-sdk package)."""

from logger import get_logger

from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage, AssistantMessage, SystemMessage

from domain.agents.agent_provider import AgentProvider
from infrastructure.agents.stock_tools import create_stock_mcp_server, TOOL_NAMES

log = get_logger(__name__)

def _format_history(messages: list[dict]) -> str:
    """Render prior turns as readable text so the agent has conversation context."""
    lines = []
    for m in messages:
        label = "User" if m["role"] == "user" else "Assistant"
        lines.append(f"{label}: {m['content']}")
    return "\n".join(lines)


class ClaudeAgent(AgentProvider):
    def __init__(self, model: str = "claude-sonnet-4-6"):
        self._model = model
        self._mcp_server = create_stock_mcp_server()

    async def chat(self, messages: list[dict], system_prompt: str) -> str:
        # Agent SDK takes a single prompt; reconstruct context from history
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
                mcp_servers={"stock-data": self._mcp_server},
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
