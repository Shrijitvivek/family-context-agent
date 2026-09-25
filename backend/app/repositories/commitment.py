# """Commitment repository.

# TODO:
# - Implement active search, duplicate-candidate search, updates, and timeline queries.
# - Load related member, document, dependency, and notification data efficiently.
# """


from datetime import date, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commitment import Commitment


class CommitmentRepository:
    """Database operations for Commitment."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
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
    ) -> Commitment:

        commitment = Commitment(
            family_id=family_id,
            member_id=member_id,
            title=title,
            category=category,
            description=description,
            amount=amount,
            due_date=due_date,
            status=status,
            priority=priority,
            source=source,
            document_id=document_id,
        )

        self.session.add(commitment)

        await self.session.flush()
        await self.session.refresh(commitment)

        return commitment

    async def get_by_id(
        self,
        commitment_id: UUID,
    ) -> Commitment | None:

        result = await self.session.execute(
            select(Commitment)
            .where(Commitment.id == commitment_id)
        )

        return result.scalar_one_or_none()

    async def get_by_family(
        self,
        family_id: UUID,
    ) -> list[Commitment]:

        result = await self.session.execute(
            select(Commitment)
            .where(Commitment.family_id == family_id)
            .order_by(Commitment.due_date.asc())
        )

        return list(result.scalars().all())

    async def get_active(
        self,
        family_id: UUID,
    ) -> list[Commitment]:

        result = await self.session.execute(
            select(Commitment)
            .where(
                Commitment.family_id == family_id,
                Commitment.status.in_(
                    ["PENDING", "SCHEDULED", "IN_PROGRESS"]
                ),
            )
            .order_by(Commitment.due_date.asc())
        )

        return list(result.scalars().all())

    async def get_upcoming(
        self,
        family_id: UUID,
        until_date: date,
    ) -> list[Commitment]:

        result = await self.session.execute(
            select(Commitment)
            .where(
                Commitment.family_id == family_id,
                Commitment.due_date <= until_date,
                Commitment.status.in_(
                    ["PENDING", "SCHEDULED", "IN_PROGRESS"]
                ),
            )
            .order_by(Commitment.due_date.asc())
        )

        return list(result.scalars().all())

    async def get_overdue(
        self,
        family_id: UUID,
        today: date,
    ) -> list[Commitment]:

        result = await self.session.execute(
            select(Commitment)
            .where(
                Commitment.family_id == family_id,
                Commitment.due_date < today,
                Commitment.status.in_(
                    ["PENDING", "SCHEDULED", "IN_PROGRESS"]
                ),
            )
            .order_by(Commitment.due_date.asc())
        )

        return list(result.scalars().all())

    async def update(
        self,
        commitment_id: UUID,
        **values,
    ) -> Commitment | None:

        commitment = await self.get_by_id(commitment_id)

        if commitment is None:
            return None

        for field, value in values.items():
            if value is not None:
                setattr(commitment, field, value)

        await self.session.flush()
        await self.session.refresh(commitment)

        return commitment

    async def complete(
        self,
        commitment_id: UUID,
    ) -> Commitment | None:

        commitment = await self.get_by_id(commitment_id)

        if commitment is None:
            return None

        commitment.status = "COMPLETED"
        commitment.completed_at = datetime.utcnow()

        await self.session.flush()
        await self.session.refresh(commitment)

        return commitment