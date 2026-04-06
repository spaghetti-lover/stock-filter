from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    stocks_context: list[dict] | None = None


class ChatResponse(BaseModel):
    response: str
    provider: str
