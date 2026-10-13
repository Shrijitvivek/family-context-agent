"""PostgreSQL integration coverage for dependency and priority lifecycles."""

from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy import delete, func, select

from app.core.constants import (
    CommitmentStatus,
    CommitmentType,
    NotificationStatus,
    NotificationType,
    Priority,
    SourceType,
)
from app.core.exceptions import DuplicateDependencyError, NotFoundError
from app.db.session import AsyncSessionLocal
from app.models.commitment import Commitment
from app.models.commitment_dependency import CommitmentDependency
from app.models.family import Family
from app.models.notification import Notification
from app.repositories.commitment import CommitmentRepository
from app.repositories.notification import NotificationRepository
from app.schemas.commitment import (
    CommitmentCreate,
    CommitmentDependencyCreate,
    CommitmentUpdate,
)
from app.services.commitment import CommitmentService
from app.services.notification import NotificationService
from app.services.priority import PriorityService
from app.tools.commitment_tools import update_commitment


TODAY = date(2026, 10, 13)


def _commitment_payload(family_id: UUID, title: str, due_date: date | None):
    return CommitmentCreate(
        family_id=family_id,
        commitment_type=CommitmentType.TASK,
        category="MEDICAL",
        title=title,
        description=f"{title} description",
        amount=Decimal("100.00"),
        due_date=due_date,
        status=CommitmentStatus.PENDING,
        priority=Priority.LOW,
        source_type=SourceType.MANUAL,
    )


async def _delete_families(session, family_ids: list[UUID]) -> None:
    await session.rollback()
    await session.execute(delete(Family).where(Family.id.in_(family_ids)))
    await session.commit()


def _priority_service(session, repository: CommitmentRepository) -> PriorityService:
    return PriorityService(
        repository,
        NotificationService(NotificationRepository(session)),
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_postgres_dependencies_drive_multi_prerequisite_attention_lifecycle() -> None:
    family_id = uuid4()
    async with AsyncSessionLocal() as session:
        session.add(Family(id=family_id, name="Dependency Priority Integration Family"))
        await session.flush()
        repository = CommitmentRepository(session)
        commitments = CommitmentService(repository)
        priorities = _priority_service(session, repository)

        try:
            prerequisite_a = await commitments.create(
                _commitment_payload(family_id, "CBC Test", None)
            )
            prerequisite_b = await commitments.create(
                _commitment_payload(family_id, "Blood Pressure Review", None)
            )
            target = await commitments.create(
                _commitment_payload(family_id, "Doctor Review", date(2026, 10, 16))
            )

            edge_a = await commitments.create_dependency(
                CommitmentDependencyCreate(
                    family_id=family_id,
                    source_commitment_id=prerequisite_a.id,
                    target_commitment_id=target.id,
                    relationship_type="MUST_COMPLETE_BEFORE",
                )
            )
            edge_b = await commitments.create_dependency(
                CommitmentDependencyCreate(
                    family_id=family_id,
                    source_commitment_id=prerequisite_b.id,
                    target_commitment_id=target.id,
                    relationship_type="MUST_COMPLETE_BEFORE",
                )
            )

            assert edge_a.family_id == family_id
            assert edge_a.source_commitment_id == prerequisite_a.id
            assert edge_a.target_commitment_id == target.id
            assert edge_a.dependency_type == "MUST_COMPLETE_BEFORE"
            assert edge_b.source_commitment_id == prerequisite_b.id
            assert edge_b.target_commitment_id == target.id

            persisted_edges = list(
                (
                    await session.scalars(
                        select(CommitmentDependency).where(
                            CommitmentDependency.family_id == family_id
                        )
                    )
                ).all()
            )
            assert len(persisted_edges) == 2
            assert {
                (edge.source_commitment_id, edge.target_commitment_id)
                for edge in persisted_edges
            } == {
                (prerequisite_a.id, target.id),
                (prerequisite_b.id, target.id),
            }

            recalculated = await priorities.recalculate(family_id, TODAY)
            assert recalculated.active_items == 3
            active = await priorities.attention_items(family_id)
            warnings = [
                item
                for item in active
                if item.notification_type == NotificationType.DEPENDENCY_WARNING
            ]
            assert {item.commitment_id for item in warnings} == {
                prerequisite_a.id,
                prerequisite_b.id,
            }
            assert all(item.priority == Priority.HIGH for item in warnings)
            assert all("Doctor Review" in item.message for item in warnings)
            # The near due date keeps the target itself in attention as well.
            assert any(
                item.commitment_id == target.id
                and item.notification_type == NotificationType.DUE_SOON
                for item in active
            )

            await update_commitment(
                commitments,
                CommitmentUpdate(
                    family_id=family_id,
                    commitment_id=prerequisite_a.id,
                    status=CommitmentStatus.COMPLETED,
                ),
            )
            after_completion = await priorities.recalculate(family_id, TODAY)
            assert after_completion.active_items == 2
            active_after_completion = await priorities.attention_items(family_id)
            remaining_warnings = [
                item
                for item in active_after_completion
                if item.notification_type == NotificationType.DEPENDENCY_WARNING
            ]
            assert [item.commitment_id for item in remaining_warnings] == [
                prerequisite_b.id
            ]
            assert all("Doctor Review" in item.message for item in remaining_warnings)

            all_notifications = list(
                (
                    await session.scalars(
                        select(Notification).where(
                            Notification.family_id == family_id
                        )
                    )
                ).all()
            )
            assert len(all_notifications) == 3
            resolved_a_warning = next(
                item
                for item in all_notifications
                if item.commitment_id == prerequisite_a.id
                and item.notification_type == NotificationType.DEPENDENCY_WARNING.value
            )
            assert resolved_a_warning.status == NotificationStatus.RESOLVED.value
            assert resolved_a_warning.resolved_at is not None

            # Repeating the same dependency is rejected and does not add a row.
            with pytest.raises(DuplicateDependencyError):
                await commitments.create_dependency(
                    CommitmentDependencyCreate(
                        family_id=family_id,
                        source_commitment_id=prerequisite_a.id,
                        target_commitment_id=target.id,
                        relationship_type="MUST_COMPLETE_BEFORE",
                    )
                )
            edge_count = await session.scalar(
                select(func.count(CommitmentDependency.id)).where(
                    CommitmentDependency.family_id == family_id
                )
            )
            assert edge_count == 2
            commitment_count = await session.scalar(
                select(func.count(Commitment.id)).where(
                    Commitment.family_id == family_id
                )
            )
            assert commitment_count == 3
        finally:
            await _delete_families(session, [family_id])


@pytest.mark.asyncio(loop_scope="session")
async def test_dependency_rejects_cross_family_missing_and_self_references() -> None:
    family_a_id, family_b_id = uuid4(), uuid4()
    async with AsyncSessionLocal() as session:
        session.add_all(
            [
                Family(id=family_a_id, name="Dependency Scope Family A"),
                Family(id=family_b_id, name="Dependency Scope Family B"),
            ]
        )
        await session.flush()
        repository = CommitmentRepository(session)
        commitments = CommitmentService(repository)

        try:
            a_source = await commitments.create(
                _commitment_payload(family_a_id, "Family A prerequisite", None)
            )
            a_target = await commitments.create(
                _commitment_payload(family_a_id, "Family A target", date(2026, 10, 16))
            )
            b_target = await commitments.create(
                _commitment_payload(family_b_id, "Family B target", date(2026, 10, 16))
            )

            valid = await commitments.create_dependency(
                CommitmentDependencyCreate(
                    family_id=family_a_id,
                    source_commitment_id=a_source.id,
                    target_commitment_id=a_target.id,
                    relationship_type="MUST_COMPLETE_BEFORE",
                )
            )
            assert valid.family_id == family_a_id

            with pytest.raises(NotFoundError):
                await commitments.create_dependency(
                    CommitmentDependencyCreate(
                        family_id=family_a_id,
                        source_commitment_id=a_source.id,
                        target_commitment_id=b_target.id,
                        relationship_type="MUST_COMPLETE_BEFORE",
                    )
                )

            missing_id = uuid4()
            with pytest.raises(NotFoundError):
                await commitments.create_dependency(
                    CommitmentDependencyCreate(
                        family_id=family_a_id,
                        source_commitment_id=missing_id,
                        target_commitment_id=a_target.id,
                        relationship_type="MUST_COMPLETE_BEFORE",
                    )
                )
            with pytest.raises(NotFoundError):
                await commitments.create_dependency(
                    CommitmentDependencyCreate(
                        family_id=family_a_id,
                        source_commitment_id=a_source.id,
                        target_commitment_id=missing_id,
                        relationship_type="MUST_COMPLETE_BEFORE",
                    )
                )

            with pytest.raises(ValidationError):
                CommitmentDependencyCreate(
                    family_id=family_a_id,
                    source_commitment_id=a_source.id,
                    target_commitment_id=a_source.id,
                    relationship_type="MUST_COMPLETE_BEFORE",
                )

            family_a_edges = await repository.list_dependency_edges(family_a_id)
            family_b_edges = await repository.list_dependency_edges(family_b_id)
            assert family_a_edges == [(a_source.id, a_target.id)]
            assert family_b_edges == []
            count = await session.scalar(
                select(func.count(CommitmentDependency.id)).where(
                    CommitmentDependency.family_id.in_([family_a_id, family_b_id])
                )
            )
            assert count == 1
        finally:
            await _delete_families(session, [family_a_id, family_b_id])


@pytest.mark.asyncio(loop_scope="session")
async def test_completing_prerequisite_does_not_leave_stale_attention() -> None:
    family_id = uuid4()
    async with AsyncSessionLocal() as session:
        session.add(Family(id=family_id, name="Completion Attention Integration Family"))
        await session.flush()
        repository = CommitmentRepository(session)
        commitments = CommitmentService(repository)
        priorities = _priority_service(session, repository)

        try:
            prerequisite = await commitments.create(
                _commitment_payload(family_id, "Stale Check Prerequisite", None)
            )
            target = await commitments.create(
                _commitment_payload(family_id, "Stale Check Appointment", date(2026, 10, 16))
            )
            await commitments.create_dependency(
                CommitmentDependencyCreate(
                    family_id=family_id,
                    source_commitment_id=prerequisite.id,
                    target_commitment_id=target.id,
                    relationship_type="MUST_COMPLETE_BEFORE",
                )
            )
            await priorities.recalculate(family_id, TODAY)

            await update_commitment(
                commitments,
                CommitmentUpdate(
                    family_id=family_id,
                    commitment_id=prerequisite.id,
                    status=CommitmentStatus.COMPLETED,
                ),
            )

            # Completion is expected to update attention as described by the
            # design flow; this service is constructed the same way as the API.
            active_after_completion = await priorities.attention_items(family_id)
            assert not any(
                item.commitment_id == prerequisite.id
                and item.notification_type == NotificationType.DEPENDENCY_WARNING
                for item in active_after_completion
            )
        finally:
            await _delete_families(session, [family_id])
