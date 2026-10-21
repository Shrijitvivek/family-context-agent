"""Application lifespan tests for APScheduler registration and shutdown."""

import asyncio
from types import SimpleNamespace

import pytest
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.jobs import scheduler as scheduler_module
from app.jobs.deadline_checks import run_deadline_checks
from app.main import app


class ObservedAsyncIOScheduler(AsyncIOScheduler):
    """Real APScheduler instance with shutdown calls recorded for assertions."""

    instances: list["ObservedAsyncIOScheduler"] = []

    def __init__(self) -> None:
        super().__init__()
        self.shutdown_calls: list[dict[str, object]] = []
        self.instances.append(self)

    def shutdown(self, **kwargs) -> None:
        self.shutdown_calls.append(kwargs)
        super().shutdown(**kwargs)


@pytest.mark.asyncio
async def test_application_lifespan_registers_one_configured_job_and_shuts_down(monkeypatch):
    ObservedAsyncIOScheduler.instances = []
    monkeypatch.setattr(scheduler_module, "_scheduler", None)
    monkeypatch.setattr(scheduler_module, "AsyncIOScheduler", ObservedAsyncIOScheduler)
    monkeypatch.setattr(
        scheduler_module,
        "get_settings",
        lambda: SimpleNamespace(
            scheduler_enabled=True,
            deadline_check_interval_minutes=17,
        ),
    )

    async with app.router.lifespan_context(app):
        assert len(ObservedAsyncIOScheduler.instances) == 1
        first = ObservedAsyncIOScheduler.instances[0]
        assert scheduler_module._scheduler is first
        assert first.running is True
        jobs = first.get_jobs()
        assert len(jobs) == 1
        [job] = jobs
        assert job.id == "deadline_checks"
        assert job.func is run_deadline_checks
        assert job.trigger.interval.total_seconds() == 17 * 60
        assert job.max_instances == 1
        assert job.coalesce is True

        # A repeated startup call while the application is active must reuse
        # the registered scheduler instead of adding a second job.
        scheduler_module.start_scheduler()
        assert len(ObservedAsyncIOScheduler.instances) == 1
        assert len(first.get_jobs()) == 1

    await asyncio.sleep(0)
    assert first.shutdown_calls == [{"wait": False}]
    assert first.running is False
    assert scheduler_module._scheduler is None

    # Entering a fresh application lifespan creates one fresh scheduler and
    # registers one job, without retaining the prior scheduler's job state.
    async with app.router.lifespan_context(app):
        assert len(ObservedAsyncIOScheduler.instances) == 2
        second = ObservedAsyncIOScheduler.instances[1]
        assert scheduler_module._scheduler is second
        assert second.running is True
        assert len(second.get_jobs()) == 1
        assert second.get_job("deadline_checks").func is run_deadline_checks

    await asyncio.sleep(0)
    assert second.shutdown_calls == [{"wait": False}]
    assert second.running is False
    assert scheduler_module._scheduler is None


@pytest.mark.asyncio
async def test_application_lifespan_does_not_start_scheduler_when_disabled(monkeypatch):
    ObservedAsyncIOScheduler.instances = []
    monkeypatch.setattr(scheduler_module, "_scheduler", None)
    monkeypatch.setattr(scheduler_module, "AsyncIOScheduler", ObservedAsyncIOScheduler)
    monkeypatch.setattr(
        scheduler_module,
        "get_settings",
        lambda: SimpleNamespace(
            scheduler_enabled=False,
            deadline_check_interval_minutes=17,
        ),
    )

    async with app.router.lifespan_context(app):
        assert ObservedAsyncIOScheduler.instances == []
        assert scheduler_module._scheduler is None

    assert ObservedAsyncIOScheduler.instances == []
    assert scheduler_module._scheduler is None
