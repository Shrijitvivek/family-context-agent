"""Chat workflow service."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.orchestrator import FamilyContextAgent
from app.agents.state import AgentState
from app.clients.ai_model import AIModelClient
from app.repositories.agent_event import AgentEventRepository
from app.repositories.commitment import CommitmentRepository
from app.repositories.expense import ExpenseRepository
from app.repositories.notification import NotificationRepository
from app.services.commitment import CommitmentService
from app.services.expense import ExpenseService
from app.services.notification import NotificationService
from app.services.priority import PriorityService
from app.tools.registry import ToolRegistry


class ChatService:
    """Coordinates chat requests with the Family Context Agent."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

        expense_repository = ExpenseRepository(session)
        commitment_repository = CommitmentRepository(session)
        notification_repository = NotificationRepository(session)

        expense_service = ExpenseService(expense_repository)
        commitment_service = CommitmentService(commitment_repository)
        notification_service = NotificationService(notification_repository)
        priority_service = PriorityService(
            commitments=commitment_repository,
            notifications=notification_service,
        )

        tool_registry = ToolRegistry(
            expense_service=expense_service,
            commitment_service=commitment_service,
            priority_service=priority_service,
        )

        self._agent = FamilyContextAgent(
            ai_client=AIModelClient(),
            tool_registry=tool_registry,
        )

        self._event_repository = AgentEventRepository(session)

    async def process_message(
        self,
        *,
        family_id: UUID,
        user_id: UUID | None,
        conversation_id: UUID | None,
        message: str,
    ) -> AgentState:
        """Run one user message through the agent."""
        state = AgentState(
            family_id=family_id,
            user_id=user_id,
            conversation_id=conversation_id,
            user_message=message,
        )

        try:
            state = await self._agent.run(state)

            await self._event_repository.add(
                family_id=family_id,
                event_type="agent_run",
                description="Family Context Agent processed a chat message.",
                event_data={
                    "conversation_id": (
                        str(conversation_id) if conversation_id else None
                    ),
                    "user_id": str(user_id) if user_id else None,
                    "message": message,
                    "tool_calls": state.tool_calls,
                    "tool_results": state.tool_results,
                    "requires_clarification": state.requires_clarification,
                },
            )

            await self._event_repository.commit()
            return state

        except Exception:
            await self._event_repository.rollback()
            raise