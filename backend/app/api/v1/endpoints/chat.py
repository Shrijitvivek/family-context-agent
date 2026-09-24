"""
Chat API endpoint.
"""

from fastapi import APIRouter, Depends

from app.agents.orchestrator import FamilyContextAgent
from app.api.dependencies import (
    get_ai_client,
    get_tool_registry,
)
from app.clients.ai_model import AIModelClient
from app.schemas.agent import (
    ChatRequest,
    ChatResponse,
    ToolCall,
)
from app.services.chat import ChatService
from app.tools.registry import ToolRegistry


router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


def get_chat_service(
    ai_client: AIModelClient = Depends(
        get_ai_client
    ),
    tool_registry: ToolRegistry = Depends(
        get_tool_registry
    ),
) -> ChatService:

    return ChatService(
        ai_client=ai_client,
        tool_registry=tool_registry,
    )


@router.post(
    "",
    response_model=ChatResponse,
)
async def chat(
    request: ChatRequest,
    service: ChatService = Depends(
        get_chat_service
    ),
):

    state = await service.process_message(
        family_id=request.family_id,
        user_id=request.user_id,
        message=request.message,
        conversation_id=request.conversation_id,
    )

    return ChatResponse(
        message=state.assistant_message,

        conversation_id=state.conversation_id,

        tool_calls=[
            ToolCall(
                name=tool["name"],
                arguments=tool["arguments"],
            )
            for tool in state.tool_calls
        ],

        requires_clarification=(
            state.requires_clarification
        ),

        metadata={
            **state.metadata,
            "tool_results": state.tool_results,
        },
    )