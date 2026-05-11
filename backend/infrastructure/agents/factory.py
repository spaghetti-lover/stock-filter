"""Factory that resolves AgentProvider from the given provider name.

provider must be one of: claude (default), openai, gemini
"""

from domain.agents.agent_provider import AgentProvider
from infrastructure.agents.mcp_config import McpConfig, ALL_TOOLS


def get_agent_provider(provider: str = "claude", mcp_config: McpConfig = ALL_TOOLS) -> AgentProvider:
    provider = provider.lower()

    if provider == "gemini":
        from infrastructure.agents.gemini_agent import GeminiAgent
        return GeminiAgent(mcp_config=mcp_config)

    from infrastructure.agents.claude_agent import ClaudeAgent
    return ClaudeAgent(mcp_config=mcp_config)
