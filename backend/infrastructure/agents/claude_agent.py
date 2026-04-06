"""Claude implementation using the Claude Agent SDK (claude-agent-sdk package)."""

from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

from domain.agents.agent_provider import AgentProvider


def _format_history(messages: list[dict]) -> str:
    """Render prior turns as readable text so the agent has conversation context."""
    lines = []
    for m in messages:
        label = "User" if m["role"] == "user" else "Assistant"
        lines.append(f"{label}: {m['content']}")
    return "\n".join(lines)


class ClaudeAgent(AgentProvider):
    def __init__(self, model: str = "claude-opus-4-6"):
        self._model = model

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
            ),
        ):
            if isinstance(message, ResultMessage):
                return message.result or ""

        return ""
