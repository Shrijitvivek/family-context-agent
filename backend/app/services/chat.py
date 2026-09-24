
"""
Chat service for the Family Context Agent.
"""

from uuid import UUID

from app.agents.orchestrator import FamilyContextAgent
from app.agents.state import AgentState
from app.clients.ai_model import AIModelClient
from app.repositories.agent_event import AgentEventRepository
from app.tools.registry import ToolRegistry


class ChatService:
    """Service responsible for running the Family Context Agent."""

    def __init__(
        self,
        ai_client: AIModelClient,
        tool_registry: ToolRegistry,
        agent_event_repository: AgentEventRepository,
    ) -> None:

        self.agent = FamilyContextAgent(
            ai_client=ai_client,
            tool_registry=tool_registry,
        )

        self.agent_event_repository = (
            agent_event_repository
        )

    async def process_message(
        self,
        *,
        family_id: UUID,
        user_id: UUID | None,
        conversation_id: UUID | None,
        message: str,
    ) -> AgentState:
        """Run one user message through the Family Context Agent."""

        # Record that the agent started processing.
        await self.agent_event_repository.create(
            family_id=family_id,
            event_type="agent_started",
            description="Family Context Agent started processing a message.",
            event_data={
                "user_id": str(user_id) if user_id else None,
                "conversation_id": (
                    str(conversation_id)
                    if conversation_id
                    else None
                ),
                "message": message,
            },
        )

        state = AgentState(
            family_id=family_id,
            user_id=user_id,
            conversation_id=conversation_id,
            user_message=message,
        )

        try:

            state = await self.agent.run(state)

            # Record successful completion.
            await self.agent_event_repository.create(
                family_id=family_id,
                event_type="agent_completed",
                description="Family Context Agent completed successfully.",
                event_data={
                    "conversation_id": (
                        str(state.conversation_id)
                        if state.conversation_id
                        else None
                    ),
                    "tool_count": len(
                        state.tool_calls
                    ),
                },
            )

            return state

        except Exception as exc:

            # Record agent failure.
            await self.agent_event_repository.create(
                family_id=family_id,
                event_type="agent_failed",
                description="Family Context Agent failed while processing the message.",
                event_data={
                    "error": str(exc),
                },
            )

            raise

