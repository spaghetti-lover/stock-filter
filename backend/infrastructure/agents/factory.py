"""Factory that resolves AgentProvider from the given provider name.

provider must be one of: claude (default), openai, gemini
"""

from domain.agents.agent_provider import AgentProvider


def get_agent_provider(provider: str = "claude") -> AgentProvider:
    provider = provider.lower()

    if provider == "openai":
        from infrastructure.agents.openai_agent import OpenAIAgent
        return OpenAIAgent()

    if provider == "gemini":
        from infrastructure.agents.gemini_agent import GeminiAgent
        return GeminiAgent()

    from infrastructure.agents.claude_agent import ClaudeAgent
    return ClaudeAgent()
