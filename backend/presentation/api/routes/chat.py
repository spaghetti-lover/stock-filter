from fastapi import APIRouter

from application.dto.chat_dto import ChatRequest, ChatResponse
from application.use_case.chat_use_case import ChatUseCase
from infrastructure.agents.factory import get_agent_provider

router = APIRouter()


def _get_use_case() -> ChatUseCase:
    return ChatUseCase(get_agent_provider())


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    return await _get_use_case().execute(request)
