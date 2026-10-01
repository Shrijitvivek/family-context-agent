"""Deadline and dependency checks.

Deterministic only: marks overdue items and syncs notifications through the
priority service. Never calls the AI model. Each recalculation uses its own
database session, so it cannot interfere with the request or job that triggered it.
"""
# backend/app/jobs/deadline_checker.py

from datetime import datetime


async def check_deadlines(db):

    """
    Check commitments whose deadlines are approaching.

    The actual query should use the Commitment model
    from Team 1.
    """

    now = datetime.utcnow()

    print(
        f"Checking commitment deadlines at {now}"
    )

    # Later:
    #
    # 1. Query pending commitments.
    # 2. Find deadlines approaching.
    # 3. Prevent duplicate notifications.
    # 4. Create notification records.

import logging
from uuid import UUID

from app.core.config import get_settings
from app.core.exceptions import FamilyContextError
from app.db.session import AsyncSessionLocal
from app.repositories.commitment import CommitmentRepository
from app.repositories.family import FamilyRepository
from app.repositories.notification import NotificationRepository
from app.services.notification import NotificationService
from app.services.priority import PriorityService
from app.utils.dates import today_in

logger = logging.getLogger(__name__)


async def refresh_priorities(family_id: UUID) -> None:
    """Recalculate one family in a fresh session. Logs and swallows domain errors.

    Used as the ``PriorityRefresher`` after commitment changes: the user's change
    is already committed, so a failure here must not turn it into an error.
    """

    async with AsyncSessionLocal() as session:
        service = PriorityService(
            CommitmentRepository(session),
            NotificationService(NotificationRepository(session)),
        )
        try:
            await service.recalculate(family_id, today_in(get_settings().family_timezone))
        except FamilyContextError:
            logger.exception("priority_refresh_failed", extra={"family_id": str(family_id)})


async def run_deadline_checks() -> int:
    """Recalculate every family; one failure doesn't stop the rest."""

    async with AsyncSessionLocal() as session:
        family_ids = [f.id for f in await FamilyRepository(session).list_families()]

    for family_id in family_ids:
        await refresh_priorities(family_id)
    return len(family_ids)
