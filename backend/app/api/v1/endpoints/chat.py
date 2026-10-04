"""Chat and natural-language input endpoints.

TODO:
- Accept a family, optional member, message, and attachment references.
- Pass validated input to the chat service and agent orchestrator.
- Return responses, clarification prompts, confirmations, and UI actions.
"""
"""Chat and natural-language input endpoints."""

from fastapi import APIRouter, Depends

from app.api.dependencies import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat import ChatService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    session: AsyncSession = Depends(get_db),
) -> ChatResponse:
    service = ChatService(session)

    state = await service.process_message(
        family_id=request.family_id,
        user_id=request.user_id,
        conversation_id=request.conversation_id,
        message=request.message,
    )

    return ChatResponse(
        conversation_id=state.conversation_id,
        message=state.assistant_message or "",
        tool_calls=state.tool_calls,
        tool_results=state.tool_results,
        requires_clarification=state.requires_clarification,
    )