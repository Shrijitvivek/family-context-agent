"""Timezone-aware date helpers."""

from datetime import date, datetime
from zoneinfo import ZoneInfo


def today_in(timezone: str) -> date:
    """Return today's date in the family's timezone, not the server's."""

    return datetime.now(ZoneInfo(timezone)).date()


def describe_due(due_date: date, today: date) -> str:
    """Human-readable distance to a due date, e.g. 'due tomorrow', 'overdue by 3 days'."""

    days = (due_date - today).days
    if days < 0:
        overdue = -days
        return f"overdue by {overdue} day{'s' if overdue != 1 else ''}"
    if days == 0:
        return "due today"
    if days == 1:
        return "due tomorrow"
    return f"due in {days} days"
