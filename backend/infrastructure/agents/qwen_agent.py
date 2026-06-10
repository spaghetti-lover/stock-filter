"""Qwen implementation using DashScope's OpenAI-compatible endpoint with LangChain MCP tool binding."""

import os

from fastapi import HTTPException
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI

from domain.agents.agent_provider import AgentProvider
from infrastructure.tools import CHAT_ALL, McpToolRegistry, ToolSet

_DASHSCOPE_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
_MAX_TOOL_ITERATIONS = 10


class QwenAgent(AgentProvider):
    def __init__(
        self,
        tool_registry: McpToolRegistry,
        model: str = "qwen-plus",
        toolset: ToolSet = CHAT_ALL,
    ):
        api_key = os.environ.get("DASHSCOPE_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="DASHSCOPE_API_KEY is not set")
        self._model = model
        self._tools: list[BaseTool] = tool_registry.tools_for(toolset)
        self._tools_by_name = {t.name: t for t in self._tools}
        llm = ChatOpenAI(
            model=model,
            base_url=_DASHSCOPE_BASE_URL,
            api_key=api_key,
        )
        self._llm = llm.bind_tools(self._tools) if self._tools else llm

    async def chat(self, messages: list[dict], system_prompt: str) -> str:
        history: list = [SystemMessage(content=system_prompt)]
        for m in messages:
            if m["role"] == "assistant":
                history.append(AIMessage(content=m["content"]))
            else:
                history.append(HumanMessage(content=m["content"]))

        try:
            for _ in range(_MAX_TOOL_ITERATIONS):
                response = await self._llm.ainvoke(history)
                history.append(response)

                tool_calls = getattr(response, "tool_calls", None) or []
                if not tool_calls:
                    return _extract_text(response.content)

                for call in tool_calls:
                    name = call.get("name", "")
                    args = call.get("args", {}) or {}
                    tool = self._tools_by_name.get(name)
                    if tool is None:
                        result = f"Error: unknown tool '{name}'"
                    else:
                        try:
                            result = await tool.ainvoke(args)
                        except Exception as exc:
                            result = f"Tool '{name}' failed: {exc}"
                    history.append(
                        ToolMessage(
                            content=_to_tool_content(result),
                            tool_call_id=call.get("id", ""),
                        )
                    )

            return "Error: exceeded tool-call iteration limit"

        except HTTPException:
            raise
        except Exception as exc:
            status = getattr(exc, "status_code", None) or getattr(exc, "http_status", None)
            if status == 429:
                raise HTTPException(status_code=429, detail=f"Qwen quota exceeded: {exc}") from exc
            raise HTTPException(status_code=502, detail=f"Qwen API error: {exc}") from exc


def _extract_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                parts.append(block.get("text", ""))
            else:
                parts.append(str(block))
        return "".join(parts)
    return str(content) if content is not None else ""


def _to_tool_content(result) -> str:
    if isinstance(result, str):
        return result
    return str(result)
