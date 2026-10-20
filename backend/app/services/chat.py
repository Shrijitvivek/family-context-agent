"""Chat workflow service."""

from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.orchestrator import FamilyContextAgent
from app.agents.state import AgentState
from app.clients.ai_model import AIModelClient
from app.core.config import get_settings
from app.repositories.agent_event import AgentEventRepository
from app.repositories.commitment import CommitmentRepository
from app.repositories.conversation import ConversationRepository
from app.repositories.document import DocumentRepository
from app.repositories.expense import ExpenseRepository
from app.repositories.family import FamilyRepository
from app.repositories.notification import NotificationRepository
from app.services.commitment import CommitmentService
from app.services.context import ContextService
from app.services.expense import ExpenseService
from app.services.notification import NotificationService
from app.services.priority import PriorityService
from app.tools.registry import ToolRegistry
from app.utils.dates import today_in


class ChatService:
    """Coordinates chat requests with the Family Context Agent."""

    def __init__(
        self,
        session: AsyncSession,
        today: date | None = None,
    ) -> None:
        self._session = session
        self._today = today or today_in(get_settings().family_timezone)

        expense_repository = ExpenseRepository(session)
        commitment_repository = CommitmentRepository(session)
        notification_repository = NotificationRepository(session)
        family_repository = FamilyRepository(session)

        expense_service = ExpenseService(expense_repository)
        context_service = ContextService(
            families=family_repository,
            commitments=commitment_repository,
        )
        notification_service = NotificationService(notification_repository)

        priority_service = PriorityService(
            commitments=commitment_repository,
            notifications=notification_service,
        )

        async def refresh_priorities(family_id: UUID) -> None:
            await priority_service.recalculate(
                family_id,
                self._today or today_in(get_settings().family_timezone),
            )

        commitment_service = CommitmentService(
            commitment_repository,
            on_change=refresh_priorities,
        )

        tool_registry = ToolRegistry(
            expense_service=expense_service,
            commitment_service=commitment_service,
            priority_service=priority_service,
        )

        self._context_service = ContextService(
            families=family_repository,
            commitments=commitment_repository,
        )

        self._agent = FamilyContextAgent(
            ai_client=AIModelClient(),
            tool_registry=tool_registry,
        )

        self._conversation_repository = ConversationRepository(session)
        self._document_repository = DocumentRepository(session)
        self._event_repository = AgentEventRepository(session)

    async def get_history(
        self,
        *,
        family_id: UUID,
        conversation_id: UUID,
    ):
        """Return the stored messages for an existing conversation."""

        await self._conversation_repository.get(
            family_id,
            conversation_id,
        )

        return await self._conversation_repository.recent_messages(
            conversation_id,
            limit=100,
        )
    async def process_message(
        self,
        *,
        family_id: UUID,
        member_id: UUID | None,
        conversation_id: UUID | None,
        message: str,
        document_id: UUID | None = None,
    ) -> AgentState:
        """Run one user message through the agent."""

        current_today = getattr(self, "_today", None) or today_in(
            get_settings().family_timezone
        )

        document = None

        if document_id:
            document = await self._document_repository.get(
                family_id,
                document_id,
            )

        if conversation_id:
            conversation = await self._conversation_repository.get(
                family_id,
                conversation_id,
            )
        else:
            conversation = await self._conversation_repository.create(
                family_id
            )
            conversation_id = conversation.id

        history = await self._conversation_repository.recent_messages(
            conversation_id,
            limit=20,
        )

        await self._conversation_repository.add_message(
            conversation_id=conversation_id,
            role="user",
            content=message,
        )
        
        household_context = await self._context_service.build(
            family_id=family_id,
            member_id=member_id,
        )

        state = AgentState(
    family_id=family_id,
    member_id=member_id,
    conversation_id=conversation_id,
    user_message=message,
    household_context=household_context.to_prompt(), 
    history=[
        {
            "role": item.role,
            "content": item.content,
        }
        for item in history
    ]
    + [
        {
            "role": "user",
            "content": message,
        }
    ],
    metadata={
        "today": current_today.isoformat(),
        "document": {
            "file_name": document.file_name,
            "document_type": document.document_type,
            "processing_status": document.processing_status,
            "extracted_text": document.extracted_text,
            "extracted_data": document.extracted_data,
        }
        if document
        else None,
    },
)
        try:
            state = await self._agent.run(state)

            # Log intent detection
            await self._event_repository.add(
                family_id=family_id,
                event_type="INTENT_DETECTED",
                description="Agent processed the incoming request.",
                event_data={
                    "conversation_id": (
                        str(conversation_id) if conversation_id else None
                    ),
                    "member_id": str(member_id) if member_id else None,
                    "tool_count": len(state.tool_calls),
                },
            )

            # Save the assistant's response
            if state.assistant_message:
                await self._conversation_repository.add_message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=state.assistant_message,
                )

            # Log tool calls and their results
            for index, call in enumerate(state.tool_calls):
                tool_name = call.get("name", "unknown")

                result_item = (
                    state.tool_results[index]
                    if index < len(state.tool_results)
                    else {}
                )

                result = result_item.get("result", {})

                
                if isinstance(result, dict):
                    succeeded = result.get("success") is not False
                else:
                    succeeded = getattr(result, "success", True) is not False


                if succeeded is None:
                    succeeded = False

                event_data = {
                    "conversation_id": (
                        str(conversation_id) if conversation_id else None
                    ),
                    "tool_name": tool_name,
                    "success": bool(succeeded),
                }

                # TOOL_CALLED
                await self._event_repository.add(
                    family_id=family_id,
                    event_type="TOOL_CALLED",
                    description=f"Tool {tool_name} was called.",
                    event_data={
                        "conversation_id": (
                            str(conversation_id)
                            if conversation_id
                            else None
                        ),
                        "tool_name": tool_name,
                    },
                )

                # TOOL_SUCCEEDED or TOOL_FAILED
                await self._event_repository.add(
                    family_id=family_id,
                    event_type=(
                        "TOOL_SUCCEEDED"
                        if succeeded
                        else "TOOL_FAILED"
                    ),
                    description=(
                        f"Tool {tool_name} "
                        f"{'succeeded' if succeeded else 'failed'}."
                    ),
                    event_data=event_data,
                )

                # Commitment creation event
                if succeeded and tool_name == "create_commitment":
                    await self._event_repository.add(
                        family_id=family_id,
                        event_type="COMMITMENT_CREATED",
                        description="A commitment was created.",
                        event_data=event_data,
                    )

                # Commitment update event
                elif succeeded and tool_name == "update_commitment":
                    await self._event_repository.add(
                        family_id=family_id,
                        event_type="COMMITMENT_UPDATED",
                        description="A commitment was updated.",
                        event_data=event_data,
                    )

            # Log document processing
            if document_id:
                await self._event_repository.add(
                    family_id=family_id,
                    event_type="DOCUMENT_PROCESSED",
                    description="A document was included in the agent request.",
                    event_data={
                        "conversation_id": (
                            str(conversation_id)
                            if conversation_id
                            else None
                        ),
                        "document_id": str(document_id),
                    },
                )

            # Commit conversation and event changes
            await self._event_repository.commit()

            return state

        except Exception as exc:
            # Roll back failed request changes
            await self._event_repository.rollback()

            # Record the error in a separate transaction
            try:
                await self._event_repository.add(
                    family_id=family_id,
                    event_type="ERROR",
                    description="Agent request failed.",
                    event_data={
                        "conversation_id": (
                            str(conversation_id)
                            if conversation_id
                            else None
                        ),
                        "error_type": type(exc).__name__,
                    },
                )

                await self._event_repository.commit()

            except Exception:
                await self._event_repository.rollback()

            raise