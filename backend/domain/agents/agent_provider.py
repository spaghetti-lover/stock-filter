from abc import ABC, abstractmethod


class AgentProvider(ABC):
    """Port: contract every LLM backend must satisfy."""

    @abstractmethod
    async def chat(
        self,
        messages: list[dict],
        system_prompt: str,
    ) -> str:
        """
        Args:
            messages: conversation history, each item {"role": "user"|"assistant", "content": str}
            system_prompt: instructions prepended to the conversation
        Returns:
            the assistant's reply text
        """
