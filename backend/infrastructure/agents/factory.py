"""Factory that resolves AgentProvider from the LLM_PROVIDER environment variable.

Set LLM_PROVIDER to one of: claude (default), openai, gemini
"""

import os

from domain.agents.agent_provider import AgentProvider


def get_agent_provider() -> AgentProvider:
    provider = os.getenv("LLM_PROVIDER", "claude").lower()

    if provider == "openai":
        from infrastructure.agents.openai_agent import OpenAIAgent
        return OpenAIAgent()

    if provider == "gemini":
        from infrastructure.agents.gemini_agent import GeminiAgent
        return GeminiAgent()

    from infrastructure.agents.claude_agent import ClaudeAgent
    return ClaudeAgent()
