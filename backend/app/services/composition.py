"""Shared production composition for commitment-related services."""

from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.repositories.commitment import CommitmentRepository
from app.repositories.notification import NotificationRepository
from app.services.commitment import CommitmentService
from app.services.dependency import DependencyService
from app.services.notification import NotificationService
from app.services.priority import PriorityRefresher, PriorityService
from app.utils.dates import today_in


def priority_refresher(session: AsyncSession) -> PriorityRefresher:
    """Build the shared, family-scoped refresh callback for mutations."""

    repository = CommitmentRepository(session)
    priority_service = PriorityService(
        commitments=repository,
        notifications=NotificationService(NotificationRepository(session)),
    )

    async def refresh(family_id: UUID) -> None:
        settings = get_settings()
        today: date = today_in(settings.family_timezone)
        await priority_service.recalculate(family_id, today)

    return refresh


def create_commitment_service(session: AsyncSession) -> CommitmentService:
    return CommitmentService(
        CommitmentRepository(session),
        on_change=priority_refresher(session),
    )


def create_dependency_service(session: AsyncSession) -> DependencyService:
    return DependencyService(
        CommitmentRepository(session),
        on_change=priority_refresher(session),
    )
