"""PostgreSQL integration coverage for commitment lifecycle persistence."""

from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy import delete, func, select

from app.core.constants import CommitmentStatus, CommitmentType, Priority, SourceType
from app.core.exceptions import ConflictError, InvalidStatusTransitionError, NotFoundError
from app.db.session import AsyncSessionLocal
from app.models.commitment import Commitment
from app.models.family import Family
from app.models.family_member import FamilyMember
from app.repositories.commitment import CommitmentRepository
from app.repositories.notification import NotificationRepository
from app.schemas.commitment import (
    CommitmentCreate,
    CommitmentUpdate,
    SearchCommitmentsQuery,
)
from app.services.commitment import CommitmentService
from app.services.notification import NotificationService
from app.services.priority import PriorityService
from app.tools.commitment_tools import update_commitment


async def _remove_families(session, family_ids: list[UUID]) -> None:
    await session.rollback()
    await session.execute(delete(Family).where(Family.id.in_(family_ids)))
    await session.commit()


def _create_payload(
    family_id: UUID,
    member_id: UUID,
    title: str,
    due_date: date,
) -> CommitmentCreate:
    return CommitmentCreate(
        family_id=family_id,
        member_id=member_id,
        commitment_type=CommitmentType.BILL,
        category="utilities",
        title=title,
        description=f"{title} monthly bill",
        amount=Decimal("1850.00"),
        start_date=date(2026, 10, 1),
        due_date=due_date,
        status=CommitmentStatus.PENDING,
        priority=Priority.HIGH,
        source_type=SourceType.MANUAL,
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_commitment_create_progress_reschedule_complete_and_terminal_lock() -> None:
    family_id, member_id = uuid4(), uuid4()
    initial_due_date = date(2026, 10, 20)
    rescheduled_due_date = date(2026, 10, 25)

    async with AsyncSessionLocal() as session:
        session.add_all(
            [
                Family(id=family_id, name="Commitment Lifecycle Integration Family"),
                FamilyMember(
                    id=member_id,
                    family_id=family_id,
                    name="Lifecycle Member",
                    relationship_type="PARENT",
                ),
            ]
        )
        await session.flush()
        service = CommitmentService(CommitmentRepository(session))

        try:
            created = await service.create(
                _create_payload(
                    family_id,
                    member_id,
                    "Lifecycle Electricity Bill",
                    initial_due_date,
                )
            )
            commitment_id = created.id

            count = await session.scalar(
                select(func.count(Commitment.id)).where(
                    Commitment.family_id == family_id
                )
            )
            assert count == 1
            assert created.family_id == family_id
            assert created.member_id == member_id
            assert created.title == "Lifecycle Electricity Bill"
            assert created.description == "Lifecycle Electricity Bill monthly bill"
            assert created.amount == Decimal("1850.00")
            assert created.status == CommitmentStatus.PENDING.value
            assert created.due_date == initial_due_date
            assert created.priority == Priority.HIGH.value

            await update_commitment(
                service,
                CommitmentUpdate(
                    family_id=family_id,
                    commitment_id=commitment_id,
                    status=CommitmentStatus.IN_PROGRESS,
                ),
            )
            in_progress = await service.get(family_id, commitment_id)
            assert in_progress.id == commitment_id
            assert in_progress.status == CommitmentStatus.IN_PROGRESS.value

            await update_commitment(
                service,
                CommitmentUpdate(
                    family_id=family_id,
                    commitment_id=commitment_id,
                    due_date=rescheduled_due_date,
                ),
            )
            rescheduled = await service.get(family_id, commitment_id)
            assert rescheduled.id == commitment_id
            assert rescheduled.status == CommitmentStatus.IN_PROGRESS.value
            assert rescheduled.due_date == rescheduled_due_date

            await update_commitment(
                service,
                CommitmentUpdate(
                    family_id=family_id,
                    commitment_id=commitment_id,
                    status=CommitmentStatus.COMPLETED,
                ),
            )
            completed = await service.get(family_id, commitment_id)
            assert completed.id == commitment_id
            assert completed.status == CommitmentStatus.COMPLETED.value
            assert completed.completed_at is not None

            # A completed commitment is documented as locked against changes.
            with pytest.raises(ConflictError):
                await update_commitment(
                    service,
                    CommitmentUpdate(
                        family_id=family_id,
                        commitment_id=commitment_id,
                        amount=Decimal("2000.00"),
                    ),
                )

            rows = list(
                (
                    await session.scalars(
                        select(Commitment).where(
                            Commitment.family_id == family_id
                        )
                    )
                ).all()
            )
            assert len(rows) == 1
            assert rows[0].id == commitment_id
            assert rows[0].status == CommitmentStatus.COMPLETED.value
            assert rows[0].amount == Decimal("1850.00")
            assert rows[0].due_date == rescheduled_due_date
        finally:
            await _remove_families(session, [family_id])


@pytest.mark.asyncio(loop_scope="session")
async def test_commitment_cancel_and_overdue_transitions_persist() -> None:
    family_id, member_id = uuid4(), uuid4()
    today = date(2026, 10, 13)

    async with AsyncSessionLocal() as session:
        session.add_all(
            [
                Family(id=family_id, name="Commitment State Integration Family"),
                FamilyMember(
                    id=member_id,
                    family_id=family_id,
                    name="State Member",
                    relationship_type="PARENT",
                ),
            ]
        )
        await session.flush()
        repository = CommitmentRepository(session)
        service = CommitmentService(repository)

        try:
            cancelled = await service.create(
                _create_payload(
                    family_id,
                    member_id,
                    "Cancelled Internet Bill",
                    date(2026, 10, 20),
                )
            )
            await update_commitment(
                service,
                CommitmentUpdate(
                    family_id=family_id,
                    commitment_id=cancelled.id,
                    status=CommitmentStatus.CANCELLED,
                ),
            )
            cancelled_row = await service.get(family_id, cancelled.id)
            assert cancelled_row.id == cancelled.id
            assert cancelled_row.status == CommitmentStatus.CANCELLED.value
            assert cancelled_row.completed_at is not None

            overdue = await service.create(
                _create_payload(
                    family_id,
                    member_id,
                    "Past Due Water Bill",
                    date(2026, 10, 10),
                )
            )
            priorities = PriorityService(
                repository,
                NotificationService(NotificationRepository(session)),
            )
            result = await priorities.recalculate(family_id, today)
            overdue_row = await service.get(family_id, overdue.id)
            assert result.marked_overdue == 1
            assert overdue_row.id == overdue.id
            assert overdue_row.status == CommitmentStatus.OVERDUE.value

            with pytest.raises(InvalidStatusTransitionError):
                await update_commitment(
                    service,
                    CommitmentUpdate(
                        family_id=family_id,
                        commitment_id=overdue.id,
                        status=CommitmentStatus.OVERDUE,
                    ),
                )

            rows = list(
                (
                    await session.scalars(
                        select(Commitment).where(
                            Commitment.family_id == family_id
                        )
                    )
                ).all()
            )
            assert len(rows) == 2
            assert {row.id for row in rows} == {cancelled.id, overdue.id}
        finally:
            await _remove_families(session, [family_id])


@pytest.mark.asyncio(loop_scope="session")
async def test_commitment_search_and_updates_remain_family_and_member_scoped() -> None:
    family_a_id, family_b_id = uuid4(), uuid4()
    member_a_id, member_b_id = uuid4(), uuid4()

    async with AsyncSessionLocal() as session:
        session.add_all(
            [
                Family(id=family_a_id, name="Scope Family A"),
                Family(id=family_b_id, name="Scope Family B"),
                FamilyMember(
                    id=member_a_id,
                    family_id=family_a_id,
                    name="Member A",
                    relationship_type="PARENT",
                ),
                FamilyMember(
                    id=member_b_id,
                    family_id=family_b_id,
                    name="Member B",
                    relationship_type="PARENT",
                ),
            ]
        )
        await session.flush()
        service = CommitmentService(CommitmentRepository(session))

        try:
            item_a = await service.create(
                _create_payload(
                    family_a_id,
                    member_a_id,
                    "Scoped Electricity Bill A",
                    date(2026, 10, 20),
                )
            )
            item_b = await service.create(
                _create_payload(
                    family_b_id,
                    member_b_id,
                    "Scoped Electricity Bill B",
                    date(2026, 10, 20),
                )
            )

            results_a = await service.search(
                SearchCommitmentsQuery(
                    family_id=family_a_id,
                    member_id=member_a_id,
                )
            )
            results_b = await service.search(
                SearchCommitmentsQuery(
                    family_id=family_b_id,
                    member_id=member_b_id,
                )
            )
            assert [row.id for row in results_a] == [item_a.id]
            assert [row.id for row in results_b] == [item_b.id]

            with pytest.raises(NotFoundError):
                await service.get(family_a_id, item_b.id)

            await update_commitment(
                service,
                CommitmentUpdate(
                    family_id=family_b_id,
                    commitment_id=item_b.id,
                    status=CommitmentStatus.IN_PROGRESS,
                ),
            )
            unchanged_a = await service.get(family_a_id, item_a.id)
            updated_b = await service.get(family_b_id, item_b.id)
            assert unchanged_a.status == CommitmentStatus.PENDING.value
            assert updated_b.status == CommitmentStatus.IN_PROGRESS.value
            assert updated_b.member_id == member_b_id

            counts = {
                family_a_id: await session.scalar(
                    select(func.count(Commitment.id)).where(
                        Commitment.family_id == family_a_id
                    )
                ),
                family_b_id: await session.scalar(
                    select(func.count(Commitment.id)).where(
                        Commitment.family_id == family_b_id
                    )
                ),
            }
            assert counts == {family_a_id: 1, family_b_id: 1}
        finally:
            await _remove_families(session, [family_a_id, family_b_id])
