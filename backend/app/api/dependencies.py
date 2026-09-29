
"""
FastAPI dependencies for database-backed services and tools.
"""
Each provider builds a request-scoped service on top of one database session.
Keep these thin: no business rules belong here.
"""

from datetime import date
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.ai_model import AIModelClient
from app.db.session import get_db
from app.repositories.agent_event import AgentEventRepository
from app.repositories.commitment import CommitmentRepository
from app.repositories.expense import ExpenseRepository
from app.services.commitment import CommitmentService
from app.services.expense import ExpenseService
from app.tools.registry import ToolRegistry


async def get_tool_registry(
    db: AsyncSession = Depends(get_db),
) -> ToolRegistry:

    expense_repository = ExpenseRepository(
        db
    )

    commitment_repository = CommitmentRepository(
        db
    )

    expense_service = ExpenseService(
        expense_repository
    )

    commitment_service = CommitmentService(
        commitment_repository
    )

    return ToolRegistry(
        expense_service=expense_service,
        commitment_service=commitment_service,
    )


async def get_agent_event_repository(
    db: AsyncSession = Depends(get_db),
) -> AgentEventRepository:

    return AgentEventRepository(db)


def get_ai_client() -> AIModelClient:

    return AIModelClient()
from app.agents.orchestrator import FamilyContextOrchestrator
from app.clients.ai_model import AIModelClient, ModelClient
from app.clients.storage import LocalStorage, StorageClient
from app.core.config import get_settings
from app.db.session import get_db
from app.jobs.deadline_checks import refresh_priorities
from app.repositories.commitment import CommitmentRepository
from app.repositories.conversation import ConversationRepository
from app.repositories.document import DocumentRepository
from app.repositories.expense import ExpenseRepository
from app.repositories.family import FamilyRepository
from app.repositories.notification import NotificationRepository
from app.services.chat import ChatService
from app.services.commitment import CommitmentService
from app.services.context import ContextService
from app.services.demo import DemoService
from app.services.dependency import DependencyService
from app.services.document import DocumentService
from app.services.expense import ExpenseService
from app.services.family import FamilyService
from app.services.notification import NotificationService
from app.services.priority import PriorityService
from app.services.timeline import TimelineService
from app.tools.registry import ToolRegistry
from app.utils.dates import today_in

DbSession = Annotated[AsyncSession, Depends(get_db)]


# Every commitment/dependency change, from the API, the agent, or a confirmed
# document, refreshes priorities the same way.
def get_commitment_service(session: DbSession) -> CommitmentService:
    return CommitmentService(CommitmentRepository(session), refresh_priorities)


def get_dependency_service(session: DbSession) -> DependencyService:
    return DependencyService(CommitmentRepository(session), refresh_priorities)


def get_expense_service(session: DbSession) -> ExpenseService:
    return ExpenseService(ExpenseRepository(session))


def get_family_service(session: DbSession) -> FamilyService:
    return FamilyService(FamilyRepository(session))


def get_timeline_service(session: DbSession) -> TimelineService:
    return TimelineService(CommitmentRepository(session))


CommitmentServiceDep = Annotated[CommitmentService, Depends(get_commitment_service)]
DependencyServiceDep = Annotated[DependencyService, Depends(get_dependency_service)]
ExpenseServiceDep = Annotated[ExpenseService, Depends(get_expense_service)]
FamilyServiceDep = Annotated[FamilyService, Depends(get_family_service)]
TimelineServiceDep = Annotated[TimelineService, Depends(get_timeline_service)]


# --- Agent, documents, priorities, and demo -----------------------------------------


def get_model_client() -> ModelClient:
    return AIModelClient()


def get_storage() -> StorageClient:
    return LocalStorage()


def get_today() -> date:
    """Today's date in the household timezone (overridable in tests)."""

    return today_in(get_settings().family_timezone)


def get_priority_service(session: DbSession) -> PriorityService:
    return PriorityService(
        CommitmentRepository(session), NotificationService(NotificationRepository(session))
    )


PriorityServiceDep = Annotated[PriorityService, Depends(get_priority_service)]
ModelClientDep = Annotated[ModelClient, Depends(get_model_client)]
TodayDep = Annotated[date, Depends(get_today)]


def get_chat_service(
    session: DbSession, model: ModelClientDep, priorities: PriorityServiceDep
) -> ChatService:
    commitments = CommitmentRepository(session)
    registry = ToolRegistry(
        ExpenseService(ExpenseRepository(session)),
        CommitmentService(commitments, refresh_priorities),
        priorities,
    )
    return ChatService(
        conversations=ConversationRepository(session),
        context=ContextService(FamilyRepository(session), commitments),
        orchestrator=FamilyContextOrchestrator(registry),
        model=model,
        today=get_today,
    )


def get_document_service(
    session: DbSession,
    model: ModelClientDep,
    storage: Annotated[StorageClient, Depends(get_storage)],
) -> DocumentService:
    settings = get_settings()
    commitments = CommitmentRepository(session)
    return DocumentService(
        DocumentRepository(session),
        commitments,
        CommitmentService(commitments, refresh_priorities),
        storage,
        model,
        allowed_types=settings.allowed_upload_type_set,
        max_bytes=settings.max_upload_size_mb * 1024 * 1024,
    )


def get_demo_service(session: DbSession, priorities: PriorityServiceDep) -> DemoService:
    return DemoService(
        FamilyRepository(session), priorities, get_settings().demo_scenario_dir
    )


ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]
DocumentServiceDep = Annotated[DocumentService, Depends(get_document_service)]
DemoServiceDep = Annotated[DemoService, Depends(get_demo_service)]
