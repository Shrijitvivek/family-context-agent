"""Shared FastAPI dependencies."""

from datetime import date
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.orchestrator import FamilyContextAgent
from app.clients.ai_model import AIModelClient
from app.clients.storage import LocalStorage
from app.core.config import get_settings
from app.db.session import get_db
from app.repositories.commitment import CommitmentRepository
from app.repositories.document import DocumentRepository
from app.repositories.expense import ExpenseRepository
from app.repositories.family import FamilyRepository
from app.repositories.notification import NotificationRepository
from app.services.commitment import CommitmentService
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


async def get_expense_service(
    session: DbSession,
) -> ExpenseService:
    return ExpenseService(ExpenseRepository(session))


async def get_commitment_service(
    session: DbSession,
) -> CommitmentService:
    return CommitmentService(CommitmentRepository(session))


async def get_family_service(
    session: DbSession,
) -> FamilyService:
    return FamilyService(FamilyRepository(session))


async def get_dependency_service(
    session: DbSession,
) -> DependencyService:
    return DependencyService(CommitmentRepository(session))


async def get_priority_service(
    session: DbSession,
) -> PriorityService:
    return PriorityService(
        commitments=CommitmentRepository(session),
        notifications=NotificationService(
            NotificationRepository(session)
        ),
    )


async def get_document_service(
    session: DbSession,
) -> DocumentService:
    settings = get_settings()

    return DocumentService(
        documents=DocumentRepository(session),
        commitments=CommitmentRepository(session),
        commitment_service=CommitmentService(
            CommitmentRepository(session)
        ),
        storage=LocalStorage(),
        model=AIModelClient(),
        allowed_types=settings.allowed_upload_type_set,
        max_bytes=settings.max_upload_size_mb * 1024 * 1024,
    )


async def get_timeline_service(
    session: DbSession,
) -> TimelineService:
    return TimelineService(CommitmentRepository(session))


async def get_demo_service(
    session: DbSession,
) -> DemoService:
    settings = get_settings()

    return DemoService(
        families=FamilyRepository(session),
        priorities=await get_priority_service(session),
        scenario_dir=settings.demo_scenario_dir,
    )


async def get_tool_registry(
    session: DbSession,
) -> ToolRegistry:
    return ToolRegistry(
        expense_service=ExpenseService(
            ExpenseRepository(session)
        ),
        commitment_service=CommitmentService(
            CommitmentRepository(session)
        ),
        priority_service=await get_priority_service(session),
    )


async def get_family_context_agent(
    session: DbSession,
) -> FamilyContextAgent:
    return FamilyContextAgent(
        ai_client=AIModelClient(),
        tool_registry=ToolRegistry(
            expense_service=ExpenseService(
                ExpenseRepository(session)
            ),
            commitment_service=CommitmentService(
                CommitmentRepository(session)
            ),
            priority_service=await get_priority_service(session),
        ),
    )


async def get_today() -> date:
    return today_in(get_settings().family_timezone)


ExpenseServiceDep = Annotated[
    ExpenseService,
    Depends(get_expense_service),
]

CommitmentServiceDep = Annotated[
    CommitmentService,
    Depends(get_commitment_service),
]

FamilyServiceDep = Annotated[
    FamilyService,
    Depends(get_family_service),
]

DependencyServiceDep = Annotated[
    DependencyService,
    Depends(get_dependency_service),
]

DocumentServiceDep = Annotated[
    DocumentService,
    Depends(get_document_service),
]

TimelineServiceDep = Annotated[
    TimelineService,
    Depends(get_timeline_service),
]

PriorityServiceDep = Annotated[
    PriorityService,
    Depends(get_priority_service),
]

DemoServiceDep = Annotated[
    DemoService,
    Depends(get_demo_service),
]

TodayDep = Annotated[
    date,
    Depends(get_today),
]
