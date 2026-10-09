"""Chat and natural-language input endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.schemas.chat import (
    ChatHistoryMessage,
    ChatHistoryResponse,
    ChatRequest,
    ChatResponse,
)
from app.services.chat import ChatService

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    session: AsyncSession = Depends(get_db),
) -> ChatResponse:
    service = ChatService(session)

    state = await service.process_message(
        family_id=request.family_id,
        member_id=request.member_id,
        conversation_id=request.conversation_id,
        message=request.message,
        document_id=request.document_id,
    )

    return ChatResponse(
        conversation_id=state.conversation_id,
        message=state.assistant_message or "",
        tool_calls=state.tool_calls,
        tool_results=state.tool_results,
        requires_clarification=state.requires_clarification,
    )


@router.get(
    "/chat/{conversation_id}",
    response_model=ChatHistoryResponse,
)
async def get_chat_history(
    conversation_id: UUID,
    family_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> ChatHistoryResponse:
    service = ChatService(session)

    messages = await service.get_history(
        family_id=family_id,
        conversation_id=conversation_id,
    )

    return ChatHistoryResponse(
        conversation_id=conversation_id,
       messages=[
    ChatHistoryMessage(
        id=message.id,
        role=message.role,
        content=message.content,
    )
    for message in messages
],
    )