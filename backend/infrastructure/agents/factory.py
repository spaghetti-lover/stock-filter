"""Factory that resolves AgentProvider from the given provider name.

provider must be one of: claude (default), gemini, qwen
"""

from domain.agents.agent_provider import AgentProvider
from infrastructure.tools import CHAT_ALL, McpToolRegistry, ToolSet


def get_agent_provider(
    provider: str = "claude",
    toolset: ToolSet = CHAT_ALL,
    model: str | None = None,
    tool_registry: McpToolRegistry | None = None,
) -> AgentProvider:
    provider = provider.lower()
    model_kwarg = {"model": model} if model else {}

    if provider == "gemini":
        from infrastructure.agents.gemini_agent import GeminiAgent
        return GeminiAgent(toolset=toolset, **model_kwarg)

    if provider == "qwen":
        from fastapi import HTTPException
        from infrastructure.agents.qwen_agent import QwenAgent
        if tool_registry is None:
            raise HTTPException(
                status_code=500,
                detail="QwenAgent requires a tool_registry (resolve from app.state.tool_registry).",
            )
        return QwenAgent(tool_registry=tool_registry, toolset=toolset, **model_kwarg)

    from infrastructure.agents.claude_agent import ClaudeAgent
    return ClaudeAgent(toolset=toolset, **model_kwarg)
