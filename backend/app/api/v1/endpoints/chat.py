"""Chat and natural-language input endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.schemas.agent import ChatRequest, ChatResponse, ToolCall
from app.services.chat import ChatService

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    session: AsyncSession = Depends(get_db),
) -> ChatResponse:
    state = await ChatService(session).process_message(
        family_id=request.family_id,
        user_id=request.user_id,
        conversation_id=request.conversation_id,
        message=request.message,
    )

    return ChatResponse(
        message=state.assistant_message or "",
        conversation_id=state.conversation_id,
        tool_calls=[
            ToolCall(name=tool["name"], arguments=tool["arguments"])
            for tool in state.tool_calls
        ],
        requires_clarification=state.requires_clarification,
        metadata={**state.metadata, "tool_results": state.tool_results},
    )
