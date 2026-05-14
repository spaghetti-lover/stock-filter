"""Factory that resolves AgentProvider from the given provider name.

provider must be one of: claude (default), gemini
"""

from domain.agents.agent_provider import AgentProvider
from infrastructure.tools import ToolSet, CHAT_ALL


def get_agent_provider(provider: str = "claude", toolset: ToolSet = CHAT_ALL) -> AgentProvider:
    provider = provider.lower()

    if provider == "gemini":
        from infrastructure.agents.gemini_agent import GeminiAgent
        return GeminiAgent(toolset=toolset)

    from infrastructure.agents.claude_agent import ClaudeAgent
    return ClaudeAgent(toolset=toolset)
