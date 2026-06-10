from fastapi import APIRouter, Request

from application.dto.chat_dto import ChatRequest, ChatResponse
from application.use_case.chat_use_case import ChatUseCase
from infrastructure.agents.factory import get_agent_provider

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, fastapi_request: Request) -> ChatResponse:
    tool_registry = getattr(fastapi_request.app.state, "tool_registry", None)
    provider = get_agent_provider(
        request.provider,
        model=request.model,
        tool_registry=tool_registry,
    )
    return await ChatUseCase(provider).execute(request)
