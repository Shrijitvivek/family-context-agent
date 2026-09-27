"""Shared, persisted domain values for the Family Context Agent."""

from enum import StrEnum


class SourceType(StrEnum):
    """Where a record originated."""

    TEXT = "TEXT"
    PDF = "PDF"
    IMAGE = "IMAGE"
    MANUAL = "MANUAL"


class CommitmentType(StrEnum):
    BILL = "BILL"
    APPOINTMENT = "APPOINTMENT"
    LAB_TEST = "LAB_TEST"
    HOME_TASK = "HOME_TASK"
    TASK = "TASK"
    EDUCATION = "EDUCATION"
    DEADLINE = "DEADLINE"
    RENEWAL = "RENEWAL"


class CommitmentStatus(StrEnum):
    PENDING = "PENDING"
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"


class Priority(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class DependencyType(StrEnum):
    """MVP dependency direction: source must finish before target."""

    MUST_COMPLETE_BEFORE = "MUST_COMPLETE_BEFORE"


class NotificationStatus(StrEnum):
    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"


class NotificationType(StrEnum):
    OVERDUE = "OVERDUE"
    DUE_SOON = "DUE_SOON"
    DEPENDENCY_WARNING = "DEPENDENCY_WARNING"


ACTIVE_COMMITMENT_STATUSES = frozenset(
    {
        CommitmentStatus.PENDING.value,
        CommitmentStatus.SCHEDULED.value,
        CommitmentStatus.IN_PROGRESS.value,
        CommitmentStatus.OVERDUE.value,
    }
)
