"""Chat endpoints: natural-language input to the Family Context Agent."""

from uuid import UUID

from fastapi import APIRouter

from app.api.dependencies import ChatServiceDep
from app.schemas.chat import ChatRequest, ChatResponse, MessageRead

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def send_message(payload: ChatRequest, service: ChatServiceDep):
    return await service.handle(payload)


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageRead])
async def get_messages(conversation_id: UUID, family_id: UUID, service: ChatServiceDep):
    return await service.history(family_id, conversation_id)
