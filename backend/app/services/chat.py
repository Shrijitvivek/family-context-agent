"""
Chat service.

Creates the request-scoped Family Context Agent
and processes a user message.
"""

from uuid import UUID

from app.agents.orchestrator import FamilyContextAgent
from app.agents.state import AgentState
from app.clients.ai_model import AIModelClient
from app.tools.registry import ToolRegistry


class ChatService:

    def __init__(
        self,
        ai_client: AIModelClient,
        tool_registry: ToolRegistry,
    ) -> None:

        self.agent = FamilyContextAgent(
            ai_client=ai_client,
            tool_registry=tool_registry,
        )

    async def process_message(
        self,
        family_id: UUID,
        user_id: UUID | None,
        message: str,
        conversation_id: UUID | None = None,
    ) -> AgentState:

        state = AgentState(
            family_id=family_id,
            user_id=user_id,
            user_message=message,
            conversation_id=conversation_id,
        )

        return await self.agent.run(state)