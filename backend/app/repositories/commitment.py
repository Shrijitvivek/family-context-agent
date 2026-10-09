"""Database access used by commitment creation and duplicate detection."""

from datetime import date
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ACTIVE_COMMITMENT_STATUSES, CommitmentType
from app.core.exceptions import NotFoundError, ScopeViolationError
from app.models.commitment import Commitment
from app.models.commitment_dependency import CommitmentDependency
from app.models.document import Document
from app.models.family import Family
from app.models.family_member import FamilyMember
from app.repositories.query import build_filters, require_family_scope
from app.schemas.commitment import (
    CommitmentDependencyCreate,
    CommitmentUpdate,
    GetFamilyPrioritiesQuery,
    SearchCommitmentsQuery,
)


class CommitmentRepository:
    """Only exposes constrained operations needed by ``create_commitment``."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def assert_scope(
        self,
        family_id: UUID,
        *,
        member_id: UUID | None = None,
        document_id: UUID | None = None,
    ) -> None:
        family = await self._session.scalar(
            select(Family.id).where(Family.id == family_id)
        )

        if family is None:
            raise NotFoundError("Family", family_id)

        if member_id is not None:
            member_family_id = await self._session.scalar(
                select(FamilyMember.family_id).where(
                    FamilyMember.id == member_id
                )
            )

            if member_family_id is None:
                raise NotFoundError("Family member", member_id)

            if member_family_id != family_id:
                raise ScopeViolationError(
                    "Family member",
                    member_id,
                    family_id,
                )

        if document_id is not None:
            document_family_id = await self._session.scalar(
                select(Document.family_id).where(
                    Document.id == document_id
                )
            )

            if document_family_id is None:
                raise NotFoundError("Document", document_id)

            if document_family_id != family_id:
                raise ScopeViolationError(
                    "Document",
                    document_id,
                    family_id,
                )

    async def find_likely_duplicates(
        self,
        *,
        family_id: UUID,
        title: str,
        commitment_type: CommitmentType,
        category: str | None,
        due_date: date | None,
    ) -> list[Commitment]:
        """Return active records sharing a family's normalized commitment identity.

        The comparison deliberately does not use amount. A changed amount is often
        a correction to the same bill, not a signal to create a second item.
        """

        conditions = [
            Commitment.family_id == family_id,
            Commitment.status.in_(ACTIVE_COMMITMENT_STATUSES),
            Commitment.commitment_type == commitment_type.value,
            func.lower(Commitment.title) == title.casefold(),
        ]

        if category is None:
            conditions.append(Commitment.category.is_(None))
        else:
            conditions.append(Commitment.category == category)

        if due_date is None:
            conditions.append(Commitment.due_date.is_(None))
        else:
            conditions.append(Commitment.due_date == due_date)

        statement = (
            select(Commitment)
            .where(*conditions)
            .order_by(Commitment.created_at.desc())
        )

        return list((await self._session.scalars(statement)).all())

    async def search(
        self,
        query: SearchCommitmentsQuery,
    ) -> list[Commitment]:
        """Search commitments based on provided filters."""

        conditions = build_filters(
            Commitment.family_id == query.family_id,
            (
                Commitment.member_id == query.member_id
                if query.member_id is not None
                else None
            ),
            (
                Commitment.commitment_type == query.commitment_type.value
                if query.commitment_type is not None
                else None
            ),
            (
                Commitment.status == query.status.value
                if query.status is not None
                else None
            ),
            (
                Commitment.category == query.category
                if query.category is not None
                else None
            ),
            (
                Commitment.due_date <= query.due_before
                if query.due_before is not None
                else None
            ),
            (
                Commitment.due_date >= query.due_after
                if query.due_after is not None
                else None
            ),
            (
                Commitment.title.ilike(f"%{query.title_query}%")
                if query.title_query is not None
                else None
            ),
        )

        statement = (
            select(Commitment)
            .where(*conditions)
            .order_by(
                Commitment.due_date.asc().nulls_last(),
                Commitment.created_at.desc(),
            )
        )

        return list((await self._session.scalars(statement)).all())

    async def update(
        self,
        payload: CommitmentUpdate,
    ) -> Commitment:
        """Update an existing commitment."""

        commitment = await self._session.get(
            Commitment,
            payload.commitment_id,
        )

        if commitment is None or commitment.family_id != payload.family_id:
            raise NotFoundError(
                "Commitment",
                payload.commitment_id,
            )

        if payload.status is not None:
            commitment.status = payload.status.value

            if payload.status.value in ("COMPLETED", "CANCELLED"):
                commitment.completed_at = func.now()

        if payload.priority is not None:
            commitment.priority = payload.priority.value

        if payload.amount is not None:
            commitment.amount = payload.amount

        if payload.due_date is not None:
            commitment.due_date = payload.due_date

        # Load server-generated values (completed_at, updated_at) so callers can
        # serialise the row without an implicit lazy load in async code.
        await self._session.flush()
        await self._session.refresh(commitment)

        return commitment

    async def add_dependency(
        self,
        payload: CommitmentDependencyCreate,
    ) -> CommitmentDependency:
        # Verify both commitments exist and belong to the family.
        source = await self._session.get(
            Commitment,
            payload.source_commitment_id,
        )

        target = await self._session.get(
            Commitment,
            payload.target_commitment_id,
        )

        if not source or source.family_id != payload.family_id:
            raise NotFoundError(
                "Source commitment",
                payload.source_commitment_id,
            )

        if not target or target.family_id != payload.family_id:
            raise NotFoundError(
                "Target commitment",
                payload.target_commitment_id,
            )

        dependency = CommitmentDependency(
            family_id=payload.family_id,
            source_commitment_id=payload.source_commitment_id,
            target_commitment_id=payload.target_commitment_id,
            dependency_type=payload.relationship_type,
        )

        self._session.add(dependency)

        await self._session.flush()
        await self._session.refresh(dependency)

        return dependency

    async def get_priorities(
        self,
        query: GetFamilyPrioritiesQuery,
    ) -> list[Commitment]:
        conditions = [
            Commitment.family_id == query.family_id,
            Commitment.status.in_(
                (
                    "PENDING",
                    "IN_PROGRESS",
                    "SCHEDULED",
                    "OVERDUE",
                )
            ),
        ]

        # We define a case statement to order by priority
        # (CRITICAL -> HIGH -> MEDIUM -> LOW).
        priority_order = case(
            (Commitment.priority == "CRITICAL", 1),
            (Commitment.priority == "HIGH", 2),
            (Commitment.priority == "MEDIUM", 3),
            (Commitment.priority == "LOW", 4),
            else_=5,
        )

        statement = (
            select(Commitment)
            .where(*conditions)
            .order_by(
                priority_order,
                Commitment.due_date.asc().nulls_last(),
            )
        )

        result = await self._session.scalars(statement)

        return list(result.all())

    async def get(
        self,
        family_id: UUID,
        commitment_id: UUID,
    ) -> Commitment:
        commitment = await self._session.get(
            Commitment,
            commitment_id,
        )

        return require_family_scope(
            commitment,
            family_id,
            "Commitment",
            commitment_id,
        )

    async def dependency_exists(
        self,
        source_commitment_id: UUID,
        target_commitment_id: UUID,
        relationship_type: str,
    ) -> bool:
        existing = await self._session.scalar(
            select(CommitmentDependency.id).where(
                CommitmentDependency.source_commitment_id
                == source_commitment_id,
                CommitmentDependency.target_commitment_id
                == target_commitment_id,
                CommitmentDependency.dependency_type
                == relationship_type,
            )
        )

        return existing is not None

    async def list_dependency_edges(
        self,
        family_id: UUID,
    ) -> list[tuple[UUID, UUID]]:
        """Return (source, target) pairs for every dependency in one family."""

        statement = select(
            CommitmentDependency.source_commitment_id,
            CommitmentDependency.target_commitment_id,
        ).where(
            CommitmentDependency.family_id == family_id
        )

        return [
            (row[0], row[1])
            for row in (
                await self._session.execute(statement)
            ).all()
        ]

    async def add(
        self,
        commitment: Commitment,
    ) -> Commitment:
        self._session.add(commitment)

        await self._session.flush()
        await self._session.refresh(commitment)

        return commitment

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
