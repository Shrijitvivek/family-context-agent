"""Real-PostgreSQL tests for the scheduled deadline-check job entry point."""

from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy import delete, func, select

from app.core.constants import (
    CommitmentStatus,
    CommitmentType,
    NotificationStatus,
    NotificationType,
    Priority,
    SourceType,
)
from app.core.exceptions import PersistenceError
from app.db.session import AsyncSessionLocal
from app.jobs import deadline_checks
from app.models.commitment import Commitment
from app.models.commitment_dependency import CommitmentDependency
from app.models.family import Family
from app.models.notification import Notification
from app.repositories.commitment import CommitmentRepository
from app.repositories.family import FamilyRepository
from app.schemas.commitment import CommitmentCreate, CommitmentDependencyCreate, CommitmentUpdate
from app.services.commitment import CommitmentService
from app.services.priority import PriorityService
from app.tools.commitment_tools import update_commitment


TODAY = date(2026, 10, 13)


def _commitment_payload(
    family_id: UUID,
    title: str,
    due_date: date | None,
    *,
    priority: Priority = Priority.MEDIUM,
) -> CommitmentCreate:
    return CommitmentCreate(
        family_id=family_id,
        commitment_type=CommitmentType.TASK,
        category="HOUSEHOLD",
        title=title,
        description=title,
        amount=Decimal("100.00"),
        due_date=due_date,
        status=CommitmentStatus.PENDING,
        priority=priority,
        source_type=SourceType.MANUAL,
    )


async def _scope_job_to_families(monkeypatch, family_ids: set[UUID]) -> None:
    original_list_families = FamilyRepository.list_families

    async def list_test_families(repository):
        families = await original_list_families(repository)
        return [family for family in families if family.id in family_ids]

    monkeypatch.setattr(FamilyRepository, "list_families", list_test_families)
    monkeypatch.setattr(deadline_checks, "today_in", lambda _timezone: TODAY)


async def _delete_families(session, family_ids: list[UUID]) -> None:
    await session.rollback()
    await session.execute(delete(Family).where(Family.id.in_(family_ids)))
    await session.commit()


async def _rows_for_family(session, model, family_id: UUID):
    return list(
        (
            await session.scalars(
                select(model)
                .where(model.family_id == family_id)
                .execution_options(populate_existing=True)
            )
        ).all()
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_scheduled_job_updates_deadlines_dependencies_and_is_idempotent(monkeypatch):
    family_a_id, family_b_id = uuid4(), uuid4()
    async with AsyncSessionLocal() as session:
        session.add_all(
            [
                Family(id=family_a_id, name="Scheduled Check Family A"),
                Family(id=family_b_id, name="Scheduled Check Family B"),
            ]
        )
        await session.flush()
        commitments = CommitmentService(CommitmentRepository(session))
        await _scope_job_to_families(monkeypatch, {family_a_id, family_b_id})

        try:
            upcoming = await commitments.create(
                _commitment_payload(family_a_id, "Upcoming Household Task", date(2026, 10, 15))
            )
            overdue = await commitments.create(
                _commitment_payload(family_a_id, "Past Due Household Task", date(2026, 10, 10))
            )
            prerequisite_a = await commitments.create(
                _commitment_payload(family_a_id, "Prerequisite A", None)
            )
            prerequisite_b = await commitments.create(
                _commitment_payload(family_a_id, "Prerequisite B", None)
            )
            dependent = await commitments.create(
                _commitment_payload(family_a_id, "Dependent Appointment", date(2026, 10, 16))
            )
            completed_past = await commitments.create(
                _commitment_payload(family_a_id, "Completed Past Task", date(2026, 10, 9))
            )
            cancelled_past = await commitments.create(
                _commitment_payload(family_a_id, "Cancelled Past Task", date(2026, 10, 8))
            )
            family_b_due = await commitments.create(
                _commitment_payload(family_b_id, "Family B Upcoming Task", date(2026, 10, 15))
            )

            await commitments.create_dependency(
                CommitmentDependencyCreate(
                    family_id=family_a_id,
                    source_commitment_id=prerequisite_a.id,
                    target_commitment_id=dependent.id,
                    relationship_type="MUST_COMPLETE_BEFORE",
                )
            )
            await commitments.create_dependency(
                CommitmentDependencyCreate(
                    family_id=family_a_id,
                    source_commitment_id=prerequisite_b.id,
                    target_commitment_id=dependent.id,
                    relationship_type="MUST_COMPLETE_BEFORE",
                )
            )
            await commitments.update(
                CommitmentUpdate(
                    family_id=family_a_id,
                    commitment_id=completed_past.id,
                    status=CommitmentStatus.COMPLETED,
                )
            )
            await commitments.update(
                CommitmentUpdate(
                    family_id=family_a_id,
                    commitment_id=cancelled_past.id,
                    status=CommitmentStatus.CANCELLED,
                )
            )

            # Exercise the exact coroutine registered as the APScheduler job.
            processed = await deadline_checks.run_deadline_checks()
            assert processed == 2

            updated_overdue = await session.get(Commitment, overdue.id)
            await session.refresh(updated_overdue)
            assert updated_overdue.status == CommitmentStatus.OVERDUE.value
            assert updated_overdue.due_date == date(2026, 10, 10)
            assert (await session.get(Commitment, upcoming.id)).status == CommitmentStatus.PENDING.value

            family_a_notifications = await _rows_for_family(session, Notification, family_a_id)
            active_a = [
                item
                for item in family_a_notifications
                if item.status == NotificationStatus.ACTIVE.value
            ]
            assert len(active_a) == 5
            assert any(
                item.commitment_id == upcoming.id
                and item.notification_type == NotificationType.DUE_SOON.value
                for item in active_a
            )
            assert any(
                item.commitment_id == overdue.id
                and item.notification_type == NotificationType.OVERDUE.value
                and item.priority == Priority.CRITICAL.value
                for item in active_a
            )
            active_dependency_warnings = [
                item
                for item in active_a
                if item.notification_type == NotificationType.DEPENDENCY_WARNING.value
            ]
            assert {item.commitment_id for item in active_dependency_warnings} == {
                prerequisite_a.id,
                prerequisite_b.id,
            }
            assert all("Dependent Appointment" in item.message for item in active_dependency_warnings)
            assert not any(
                item.commitment_id in {completed_past.id, cancelled_past.id}
                for item in family_a_notifications
            )

            family_b_notifications = await _rows_for_family(session, Notification, family_b_id)
            assert len(family_b_notifications) == 1
            assert family_b_notifications[0].commitment_id == family_b_due.id
            assert family_b_notifications[0].notification_type == NotificationType.DUE_SOON.value

            counts_before_repeat = (
                await session.scalar(
                    select(func.count(Notification.id)).where(
                        Notification.family_id.in_([family_a_id, family_b_id])
                    )
                ),
                await session.scalar(
                    select(func.count(CommitmentDependency.id)).where(
                        CommitmentDependency.family_id == family_a_id
                    )
                ),
                await session.scalar(
                    select(func.count(Commitment.id)).where(
                        Commitment.family_id.in_([family_a_id, family_b_id])
                    )
                ),
            )
            assert counts_before_repeat == (6, 2, 8)

            await deadline_checks.run_deadline_checks()
            counts_after_repeat = (
                await session.scalar(
                    select(func.count(Notification.id)).where(
                        Notification.family_id.in_([family_a_id, family_b_id])
                    )
                ),
                await session.scalar(
                    select(func.count(CommitmentDependency.id)).where(
                        CommitmentDependency.family_id == family_a_id
                    )
                ),
                await session.scalar(
                    select(func.count(Commitment.id)).where(
                        Commitment.family_id.in_([family_a_id, family_b_id])
                    )
                ),
            )
            assert counts_after_repeat == counts_before_repeat

            # Complete A without manually recalculating. The scheduled job must
            # resolve only A's warning and retain B's warning for the same target.
            await update_commitment(
                commitments,
                CommitmentUpdate(
                    family_id=family_a_id,
                    commitment_id=prerequisite_a.id,
                    status=CommitmentStatus.COMPLETED,
                ),
            )
            await deadline_checks.run_deadline_checks()

            final_a_notifications = await _rows_for_family(session, Notification, family_a_id)
            final_active = [
                item
                for item in final_a_notifications
                if item.status == NotificationStatus.ACTIVE.value
            ]
            final_warnings = [
                item
                for item in final_active
                if item.notification_type == NotificationType.DEPENDENCY_WARNING.value
            ]
            assert [item.commitment_id for item in final_warnings] == [prerequisite_b.id]
            resolved_a_warning = next(
                item
                for item in final_a_notifications
                if item.commitment_id == prerequisite_a.id
                and item.notification_type == NotificationType.DEPENDENCY_WARNING.value
            )
            assert resolved_a_warning.status == NotificationStatus.RESOLVED.value
            assert resolved_a_warning.resolved_at is not None
            assert any(
                item.commitment_id == dependent.id
                and item.notification_type == NotificationType.DUE_SOON.value
                for item in final_active
            )
            assert len(final_a_notifications) == 5
            assert len(await _rows_for_family(session, Notification, family_b_id)) == 1
            assert await session.scalar(
                select(func.count(CommitmentDependency.id)).where(
                    CommitmentDependency.family_id == family_a_id
                )
            ) == 2
            assert await session.scalar(
                select(func.count(Commitment.id)).where(Commitment.family_id == family_a_id)
            ) == 7
        finally:
            await _delete_families(session, [family_a_id, family_b_id])


@pytest.mark.asyncio(loop_scope="session")
async def test_scheduled_job_logs_one_family_failure_and_continues(monkeypatch, caplog):
    failed_family_id, healthy_family_id = uuid4(), uuid4()
    async with AsyncSessionLocal() as session:
        session.add_all(
            [
                Family(id=failed_family_id, name="Scheduled Failure Family"),
                Family(id=healthy_family_id, name="Scheduled Healthy Family"),
            ]
        )
        await session.flush()
        commitments = CommitmentService(CommitmentRepository(session))
        failed_due = await commitments.create(
            _commitment_payload(failed_family_id, "Failure Family Upcoming Task", date(2026, 10, 15))
        )
        healthy_due = await commitments.create(
            _commitment_payload(healthy_family_id, "Healthy Family Upcoming Task", date(2026, 10, 15))
        )
        await _scope_job_to_families(monkeypatch, {failed_family_id, healthy_family_id})
        original_recalculate = PriorityService.recalculate

        async def fail_one_family(service, family_id: UUID, today: date):
            if family_id == failed_family_id:
                raise PersistenceError("recalculate family priorities")
            return await original_recalculate(service, family_id, today)

        monkeypatch.setattr(PriorityService, "recalculate", fail_one_family)

        try:
            processed = await deadline_checks.run_deadline_checks()
            assert processed == 2
            assert "priority_refresh_failed" in caplog.text
            assert any(
                getattr(record, "family_id", None) == str(failed_family_id)
                for record in caplog.records
            )

            failed_notifications = await _rows_for_family(session, Notification, failed_family_id)
            healthy_notifications = await _rows_for_family(session, Notification, healthy_family_id)
            assert failed_notifications == []
            assert len(healthy_notifications) == 1
            assert healthy_notifications[0].commitment_id == healthy_due.id
            assert (await session.get(Commitment, failed_due.id)).status == CommitmentStatus.PENDING.value
        finally:
            await _delete_families(session, [failed_family_id, healthy_family_id])
