"""OpenAI implementation using the OpenAI Agent SDK (openai-agents package)."""

from agents import Agent, Runner

from domain.agents.agent_provider import AgentProvider


class OpenAIAgent(AgentProvider):
    def __init__(self, model: str = "gpt-4o"):
        self._model = model

    async def chat(self, messages: list[dict[str, str]], system_prompt: str) -> str:
        agent = Agent(
            name="StockAssistant",
            instructions=system_prompt,
            model=self._model,
        )
        result = await Runner.run(agent, messages[-1]["content"])
        return result.final_output
