from typing import Any, Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from .base_client import BaseLLMClient, normalize_content
from .validators import validate_model

_PASSTHROUGH_KWARGS = (
    "timeout", "max_retries", "api_key", "max_tokens",
    "callbacks", "http_client", "http_async_client", "effort",
)

# Prompts built by debate/manager agents put static role + instructions
# above this marker and dynamic state below. Splitting on it lets us send
# the static prefix as a cacheable SystemMessage block so repeated calls
# within a run hit Anthropic's prompt cache.
_CACHE_SPLIT_MARKER = "\n\n---\n\n"


def _maybe_cache_split(prompt_input):
    """If the input is a single string with our split marker, convert it
    into [SystemMessage(cached), HumanMessage(dynamic)]. Otherwise return
    the input unchanged so non-prompt-cached call paths still work."""
    if not isinstance(prompt_input, str):
        return prompt_input
    if _CACHE_SPLIT_MARKER not in prompt_input:
        return prompt_input
    static_part, dynamic_part = prompt_input.split(_CACHE_SPLIT_MARKER, 1)
    static_block = {
        "type": "text",
        "text": static_part,
        "cache_control": {"type": "ephemeral"},
    }
    return [
        SystemMessage(content=[static_block]),
        HumanMessage(content=dynamic_part),
    ]


class NormalizedChatAnthropic(ChatAnthropic):
    """ChatAnthropic with normalized content output and prompt caching.

    Claude models with extended thinking or tool use return content as a
    list of typed blocks. This normalizes to string for consistent
    downstream handling. Also splits string prompts on `_CACHE_SPLIT_MARKER`
    to tag the static prefix with `cache_control: ephemeral`.
    """

    def invoke(self, input, config=None, **kwargs):
        return normalize_content(super().invoke(_maybe_cache_split(input), config, **kwargs))

    async def ainvoke(self, input, config=None, **kwargs):
        result = await super().ainvoke(_maybe_cache_split(input), config, **kwargs)
        return normalize_content(result)


class AnthropicClient(BaseLLMClient):
    """Client for Anthropic Claude models."""

    def __init__(self, model: str, base_url: Optional[str] = None, **kwargs):
        super().__init__(model, base_url, **kwargs)

    def get_llm(self) -> Any:
        """Return configured ChatAnthropic instance."""
        self.warn_if_unknown_model()
        llm_kwargs = {"model": self.model}

        if self.base_url:
            llm_kwargs["base_url"] = self.base_url

        for key in _PASSTHROUGH_KWARGS:
            if key in self.kwargs:
                llm_kwargs[key] = self.kwargs[key]

        return NormalizedChatAnthropic(**llm_kwargs)

    def validate_model(self) -> bool:
        """Validate model for Anthropic."""
        return validate_model("anthropic", self.model)
