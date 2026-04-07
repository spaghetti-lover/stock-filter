"""OpenAI implementation using the OpenAI Agent SDK (openai-agents package) with MCP."""

import sys
from pathlib import Path

from agents import Agent, Runner
from agents.mcp import MCPServerStdio

from domain.agents.agent_provider import AgentProvider

_BACKEND_DIR = str(Path(__file__).parent.parent.parent)
_MCP_SERVER_PATH = str(Path(__file__).parent.parent / "mcp" / "stock.py")


class OpenAIAgent(AgentProvider):
    def __init__(self, model: str = "gpt-4o"):
        self._model = model

    async def chat(self, messages: list[dict[str, str]], system_prompt: str) -> str:
        async with MCPServerStdio(
            params={
                "command": sys.executable,
                "args": ["-B", _MCP_SERVER_PATH],
                "env": {"PYTHONPATH": _BACKEND_DIR},
            }
        ) as mcp_server:
            agent = Agent(
                name="StockAssistant",
                instructions=system_prompt,
                model=self._model,
                mcp_servers=[mcp_server],
            )
            result = await Runner.run(agent, messages[-1]["content"])
            return result.final_output
