"""Scheduler lifecycle for periodic deadline checks.

Runs in-process. With several workers, enable it on only one
(SCHEDULER_ENABLED=false on the others) to avoid duplicate runs; the checks are
idempotent, so an accidental duplicate is harmless but wasteful.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import get_settings
from app.jobs.deadline_checks import run_deadline_checks

_scheduler: AsyncIOScheduler | None = None


def start_scheduler() -> None:
    global _scheduler
    settings = get_settings()
    if not settings.scheduler_enabled or _scheduler is not None:
        return
    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        run_deadline_checks,
        "interval",
        minutes=settings.deadline_check_interval_minutes,
        id="deadline_checks",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )
    _scheduler.start()


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
