"""Gemini implementation using the Google Gemini ADK (google-genai package)."""

import re

from fastapi import HTTPException
from google import genai
from google.genai import types
from google.genai.errors import ClientError

from domain.agents.agent_provider import AgentProvider


def _to_gemini_role(role: str) -> str:
    return "model" if role == "assistant" else "user"

class GeminiAgent(AgentProvider):
    def __init__(self, model: str = "gemini-2.5-flash"):
        self._model = model
        self._client = genai.Client()

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
            response = await self._client.aio.chats.create(
                model=self._model,
                config=types.GenerateContentConfig(system_instruction=system_prompt),
                history=history,
            ).send_message(last_message)
            return response.text or ""

        except ClientError as e:
            if e.status == 429:
                detail = (
                    f"Gemini quota exceeded: {e.args[0] if e.args else 'unknown'}"
                )
                raise HTTPException(status_code=429, detail=detail) from e
            raise HTTPException(
                status_code=502,
                detail=f"Gemini API error {e.status}: {e.args[0] if e.args else 'unknown'}",
            ) from e
