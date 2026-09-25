"""Commitment business service.

TODO:
- Create, search, update, complete, reschedule, correct, and cancel commitments.
- Detect likely duplicates before creation.
- Enforce allowed status transitions and resolve related notifications.
"""


from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.commitment_repository import CommitmentRepository


class CommitmentService:
    """Business logic for commitments."""

    VALID_STATUSES = {
        "PENDING",
        "SCHEDULED",
        "IN_PROGRESS",
        "COMPLETED",
        "OVERDUE",
        "CANCELLED",
    }

    VALID_PRIORITIES = {
        "LOW",
        "MEDIUM",
        "HIGH",
    }

    def __init__(self, session: AsyncSession):
        self.repository = CommitmentRepository(session)
        self.session = session

    async def create_commitment(
        self,
        family_id: UUID,
        title: str,
        category: str,
        member_id: UUID | None = None,
        description: str | None = None,
        amount=None,
        due_date: date | None = None,
        status: str = "PENDING",
        priority: str = "MEDIUM",
        source: str | None = None,
        document_id: UUID | None = None,
    ):

        if not title.strip():
            raise ValueError("Commitment title is required.")

        if status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status: {status}")

        if priority not in self.VALID_PRIORITIES:
            raise ValueError(f"Invalid priority: {priority}")

        commitment = await self.repository.create(
            family_id=family_id,
            title=title,
            category=category,
            member_id=member_id,
            description=description,
            amount=amount,
            due_date=due_date,
            status=status,
            priority=priority,
            source=source,
            document_id=document_id,
        )

        await self.session.commit()

        return commitment

    async def get_commitment(
        self,
        commitment_id: UUID,
    ):

        return await self.repository.get_by_id(commitment_id)

    async def get_family_commitments(
        self,
        family_id: UUID,
    ):

        return await self.repository.get_by_family(family_id)

    async def get_active_commitments(
        self,
        family_id: UUID,
    ):

        return await self.repository.get_active(family_id)

    async def get_upcoming_commitments(
        self,
        family_id: UUID,
        until_date: date,
    ):

        return await self.repository.get_upcoming(
            family_id,
            until_date,
        )

    async def get_overdue_commitments(
        self,
        family_id: UUID,
        today: date,
    ):

        return await self.repository.get_overdue(
            family_id,
            today,
        )

    async def complete_commitment(
        self,
        commitment_id: UUID,
    ):

        commitment = await self.repository.complete(
            commitment_id
        )

        if commitment is None:
            raise ValueError("Commitment not found.")

        await self.session.commit()

        return commitment

    async def update_commitment(
        self,
        commitment_id: UUID,
        **values,
    ):

        if "status" in values:
            if values["status"] not in self.VALID_STATUSES:
                raise ValueError("Invalid commitment status.")

        if "priority" in values:
            if values["priority"] not in self.VALID_PRIORITIES:
                raise ValueError("Invalid commitment priority.")

        commitment = await self.repository.update(
            commitment_id,
            **values,
        )

        if commitment is None:
            raise ValueError("Commitment not found.")

        await self.session.commit()

        return commitment