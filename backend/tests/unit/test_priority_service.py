"""Priority engine and notification sync unit tests."""

from datetime import date, timedelta
from uuid import UUID, uuid4

import pytest
from app.core.constants import NotificationType, Priority
from app.models.commitment import Commitment
from app.models.notification import Notification
from app.services.notification import NotificationService
from app.services.priority import PriorityService, assess

TODAY = date(2026, 10, 10)


def make(title: str, due_in: int | None, status: str = "PENDING", priority: str = "MEDIUM"):
    return Commitment(
        id=uuid4(),
        family_id=uuid4(),
        title=title,
        commitment_type="TASK",
        status=status,
        priority=priority,
        due_date=TODAY + timedelta(days=due_in) if due_in is not None else None,
    )


def by_type(assessments, kind: NotificationType):
    return [a for a in assessments if a.notification_type == kind]


def test_overdue_is_critical_with_evidence() -> None:
    bill = make("Electricity Bill", -2)
    [item] = assess([bill], [], TODAY)
    assert item.notification_type == NotificationType.OVERDUE
    assert item.priority == Priority.CRITICAL
    assert "overdue by 2 days" in item.message
    assert "2026-10-08" in item.message


def test_due_soon_raises_to_high_but_keeps_a_higher_baseline() -> None:
    soon = make("Fasting test", 1)
    critical = make("Passport renewal", 3, priority="CRITICAL")
    later = make("Water tank", 10)
    items = {a.commitment_id: a for a in assess([soon, critical, later], [], TODAY)}
    assert items[soon.id].priority == Priority.HIGH
    assert "due tomorrow" in items[soon.id].message
    assert items[critical.id].priority == Priority.CRITICAL
    assert later.id not in items


def test_completed_and_undated_items_are_ignored() -> None:
    done = make("Paid bill", -5, status="COMPLETED")
    undated = make("Someday task", None)
    assert assess([done, undated], [], TODAY) == []


def test_incomplete_prerequisite_warns_on_the_blocker() -> None:
    photos = make("Passport photos", None)
    exam_form = make("Exam registration", 2)
    warnings = by_type(
        assess([photos, exam_form], [(photos.id, exam_form.id)], TODAY),
        NotificationType.DEPENDENCY_WARNING,
    )
    assert len(warnings) == 1
    assert warnings[0].commitment_id == photos.id
    assert warnings[0].priority == Priority.HIGH  # inherits the target's urgency
    assert "Exam registration" in warnings[0].message


def test_finished_prerequisite_or_distant_target_does_not_warn() -> None:
    done = make("Blood test", -1, status="COMPLETED")
    appointment = make("Cardiology", 2)
    photos = make("Photos", None)
    far = make("Exam", 30)
    edges = [(done.id, appointment.id), (photos.id, far.id)]
    assessments = assess([done, appointment, photos, far], edges, TODAY)
    assert by_type(assessments, NotificationType.DEPENDENCY_WARNING) == []


class FakeCommitmentRepository:
    def __init__(self, commitments, edges=()) -> None:
        self.commitments = commitments
        self.edges = list(edges)
        self.commits = 0

    async def assert_scope(self, family_id, **_) -> None:
        pass

    async def search(self, query):
        return self.commitments

    async def list_dependency_edges(self, family_id):
        return self.edges

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        raise AssertionError("rollback should not be called")


class FakeNotificationRepository:
    def __init__(self) -> None:
        self.rows: list[Notification] = []

    async def list_active(self, family_id: UUID):
        return [n for n in self.rows if n.status == "ACTIVE"]

    def add(self, notification: Notification) -> None:
        notification.id = uuid4()
        self.rows.append(notification)

    @staticmethod
    def resolve(notification: Notification) -> None:
        notification.status = "RESOLVED"

    async def flush(self) -> None:
        pass


@pytest.mark.asyncio
async def test_recalculate_marks_overdue_and_is_idempotent() -> None:
    family_id = uuid4()
    late = make("School fee", -1)
    soon = make("Electricity", 2)
    notifications = FakeNotificationRepository()
    service = PriorityService(
        FakeCommitmentRepository([late, soon]),  # type: ignore[arg-type]
        NotificationService(notifications),  # type: ignore[arg-type]
    )

    first = await service.recalculate(family_id, TODAY)
    assert late.status == "OVERDUE"
    assert first.marked_overdue == 1
    assert first.active_items == 2

    second = await service.recalculate(family_id, TODAY)
    assert second.marked_overdue == 0
    assert len(notifications.rows) == 2  # updated in place, not duplicated


@pytest.mark.asyncio
async def test_recalculate_resolves_and_reopens_after_reschedule() -> None:
    family_id = uuid4()
    bill = make("Water bill", -1)
    notifications = FakeNotificationRepository()
    service = PriorityService(
        FakeCommitmentRepository([bill]),  # type: ignore[arg-type]
        NotificationService(notifications),  # type: ignore[arg-type]
    )
    await service.recalculate(family_id, TODAY)
    assert bill.status == "OVERDUE"

    bill.due_date = TODAY + timedelta(days=20)
    result = await service.recalculate(family_id, TODAY)
    assert bill.status == "PENDING"
    assert result.reopened == 1
    assert result.active_items == 0
    assert [n.status for n in notifications.rows] == ["RESOLVED"]
