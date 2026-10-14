"""Deterministic priority engine.

Priorities come from dates and statuses only; the AI model is never consulted.
Terminal commitments have no priority.
"""

from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError

from app.core.constants import (
    ACTIVE_COMMITMENT_STATUSES,
    CommitmentStatus,
    NotificationType,
    Priority,
)
from app.core.exceptions import PersistenceError
from app.models.commitment import Commitment
from app.repositories.commitment import CommitmentRepository
from app.schemas.commitment import CommitmentRead, SearchCommitmentsQuery
from app.schemas.priority import AttentionItem, RecalculationResult
from app.services.notification import NotificationService
from app.utils.dates import describe_due

# Called with a family id after a commitment or dependency change has been committed.
# Implementations must not raise: the user's change is already saved.
PriorityRefresher = Callable[[UUID], Awaitable[None]]

DUE_SOON_DAYS = 3
DEPENDENCY_HORIZON_DAYS = 7

_RANK = {Priority.LOW: 0, Priority.MEDIUM: 1, Priority.HIGH: 2, Priority.CRITICAL: 3}
_STATUS_PRIORITY: dict[str, Priority | None] = {
    CommitmentStatus.SCHEDULED.value: Priority.LOW,
    CommitmentStatus.PENDING.value: Priority.MEDIUM,
    CommitmentStatus.IN_PROGRESS.value: Priority.HIGH,
    CommitmentStatus.OVERDUE.value: Priority.CRITICAL,
    CommitmentStatus.COMPLETED.value: None,
    CommitmentStatus.CANCELLED.value: None,
}


def priority_floor_for_status(status: str) -> Priority | None:
    return _STATUS_PRIORITY[status]


def _active_priority(commitment: Commitment) -> Priority:
    value = commitment.priority or priority_floor_for_status(commitment.status)
    return Priority(value or Priority.LOW)


def _max_priority(*values: Priority) -> Priority:
    return max(values, key=_RANK.__getitem__)


@dataclass(frozen=True)
class Assessment:
    """Why one commitment needs attention."""

    commitment_id: UUID
    notification_type: NotificationType
    priority: Priority
    title: str
    message: str


def date_priority(due_date: date | None, today: date) -> Priority:
    if due_date is None:
        return Priority.LOW
    days = (due_date - today).days
    if days < 0:
        return Priority.CRITICAL
    if days <= DUE_SOON_DAYS:
        return Priority.HIGH
    if days <= DEPENDENCY_HORIZON_DAYS:
        return Priority.MEDIUM
    return Priority.LOW


def assess(
    commitments: Iterable[Commitment],
    edges: Iterable[tuple[UUID, UUID]],
    today: date,
) -> list[Assessment]:
    """Pure function: evaluate every active commitment and dependency edge."""

    by_id = {c.id: c for c in commitments}
    results: list[Assessment] = []

    for c in by_id.values():
        if c.status not in ACTIVE_COMMITMENT_STATUSES or c.due_date is None:
            continue
        days = (c.due_date - today).days
        when = describe_due(c.due_date, today)
        if days < 0:
            results.append(
                Assessment(
                    c.id,
                    NotificationType.OVERDUE,
                    Priority.CRITICAL,
                    f"{c.title} is overdue",
                    f"{c.title} is {when} (was due {c.due_date.isoformat()}).",
                )
            )
        elif days <= DUE_SOON_DAYS:
            results.append(
                Assessment(
                    c.id,
                    NotificationType.DUE_SOON,
                    _max_priority(
                        _active_priority(c),
                        Priority.HIGH,
                    ),
                    f"{c.title} is {when}",
                    f"{c.title} is {when} ({c.due_date.isoformat()}).",
                )
            )

    for source_id, target_id in edges:
        source, target = by_id.get(source_id), by_id.get(target_id)
        if source is None or target is None:
            continue
        if source.status not in ACTIVE_COMMITMENT_STATUSES:
            continue  # prerequisite already done or cancelled
        if target.status not in ACTIVE_COMMITMENT_STATUSES or target.due_date is None:
            continue
        if (target.due_date - today).days > DEPENDENCY_HORIZON_DAYS:
            continue
        results.append(
            Assessment(
                source.id,
                NotificationType.DEPENDENCY_WARNING,
                _max_priority(
                    _active_priority(source),
                    date_priority(source.due_date, today),
                    date_priority(target.due_date, today),
                ),
                f"Finish {source.title} first",
                f"{source.title} must be completed before {target.title}, "
                f"which is {describe_due(target.due_date, today)}.",
            )
        )
    return results


class PriorityService:
    def __init__(
        self,
        commitments: CommitmentRepository,
        notifications: NotificationService,
    ) -> None:
        self._commitments = commitments
        self._notifications = notifications

    async def recalculate(self, family_id: UUID, today: date) -> RecalculationResult:
        """Mark overdue items, reopen rescheduled ones, and sync notifications.

        Idempotent: running it twice on the same day changes nothing the second time.
        """

        await self._commitments.assert_scope(family_id)
        commitments = await self._commitments.search(SearchCommitmentsQuery(family_id=family_id))
        edges = await self._commitments.list_dependency_edges(family_id)

        marked_overdue = reopened = started = 0
        for c in commitments:
            active = c.status in ACTIVE_COMMITMENT_STATUSES
            if active:
                is_past_due = c.due_date is not None and c.due_date < today
                if is_past_due and c.status != CommitmentStatus.OVERDUE:
                    c.status = CommitmentStatus.OVERDUE.value
                    marked_overdue += 1
                elif (
                    c.status == CommitmentStatus.OVERDUE
                    and c.due_date is not None
                    and not is_past_due
                ):
                    reopened += 1
                    c.status = CommitmentStatus.PENDING.value

                if c.status in {
                    CommitmentStatus.PENDING.value,
                    CommitmentStatus.SCHEDULED.value,
                }:
                    start_reached = c.start_date is not None and c.start_date <= today
                    due_soon_without_start = (
                        c.start_date is None
                        and c.due_date is not None
                        and (c.due_date - today).days <= DUE_SOON_DAYS
                    )
                    if start_reached or due_soon_without_start:
                        c.status = CommitmentStatus.IN_PROGRESS.value
                        started += 1

            status_priority = priority_floor_for_status(c.status)
            c.priority = (
                _max_priority(
                    status_priority,
                    date_priority(c.due_date, today),
                ).value
                if active and status_priority is not None
                else None
            )

        try:
            active = await self._notifications.sync(family_id, assess(commitments, edges, today))
            await self._commitments.commit()
        except SQLAlchemyError as exc:
            await self._commitments.rollback()
            raise PersistenceError("recalculate family priorities") from exc

        return RecalculationResult(
            family_id=family_id,
            marked_overdue=marked_overdue,
            reopened=reopened,
            active_items=active,
        )

    async def attention_items(self, family_id: UUID) -> list[AttentionItem]:
        """Active notifications, most urgent first, each with its commitment."""

        await self._commitments.assert_scope(family_id)
        notifications = await self._notifications.list_active(family_id)
        commitments = {
            c.id: c
            for c in await self._commitments.search(SearchCommitmentsQuery(family_id=family_id))
        }
        items = []
        for notification in notifications:
            item = AttentionItem.model_validate(notification)
            commitment = commitments.get(notification.commitment_id)
            if commitment is not None:
                item.commitment = CommitmentRead.model_validate(commitment)
            items.append(item)

        def sort_key(item: AttentionItem) -> tuple[int, date]:
            due = item.commitment.due_date if item.commitment else None
            return (-_RANK[item.priority], due or date.max)

        return sorted(items, key=sort_key)
