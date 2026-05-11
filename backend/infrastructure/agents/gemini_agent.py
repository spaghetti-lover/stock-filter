"""Gemini implementation using the Google Gemini SDK with FastMCP in-process clients."""

import os

from fastapi import HTTPException
from fastmcp import Client
from google import genai
from google.genai import types
from google.genai.errors import ClientError

from domain.agents.agent_provider import AgentProvider
from infrastructure.mcp.data import mcp as data_mcp
from infrastructure.mcp.news import mcp as news_mcp
from infrastructure.mcp.fundamentals import mcp as fundamentals_mcp


def _to_gemini_role(role: str) -> str:
    return "model" if role == "assistant" else "user"


class GeminiAgent(AgentProvider):
    def __init__(self, model: str = "gemini-2.5-flash"):
        self._model = model
        self._client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
        self._data_client = Client(data_mcp)
        self._news_client = Client(news_mcp)
        self._fundamentals_client = Client(fundamentals_mcp)

    async def chat(self, messages: list[dict], system_prompt: str) -> str:
        history: list[types.ContentOrDict] = [
            {
                "role": _to_gemini_role(m["role"]),
                "parts": [{"text": m["content"]}],
            }
            for m in messages[:-1]
        ]
        last_message = messages[-1]["content"]

        try:
            async with self._data_client, self._news_client, self._fundamentals_client:
                chat_session = self._client.aio.chats.create(
                    model=self._model,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        tools=[
                            self._data_client.session,
                            self._news_client.session,
                            self._fundamentals_client.session,
                        ],
                    ),
                    history=history,
                )
                response = await chat_session.send_message(last_message)
            return response.text or ""

        except ClientError as e:
            if e.status == 429:
                raise HTTPException(
                    status_code=429,
                    detail=f"Gemini quota exceeded: {e.args[0] if e.args else 'unknown'}",
                ) from e
            raise HTTPException(
                status_code=502,
                detail=f"Gemini API error {e.status}: {e.args[0] if e.args else 'unknown'}",
            ) from e
