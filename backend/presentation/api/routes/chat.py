from fastapi import APIRouter

from application.dto.chat_dto import ChatRequest, ChatResponse
from application.use_case.chat_use_case import ChatUseCase
from infrastructure.agents.factory import get_agent_provider

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    provider = get_agent_provider(request.provider)
    return await ChatUseCase(provider).execute(request)
