from datetime import date, datetime
from types import SimpleNamespace
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest

from app.agents.orchestrator import FamilyContextAgent
from app.agents.state import AgentState
from app.utils import dates


REFERENCE_DATE = date(2026, 10, 6)


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("I spent 100 on lunch", date(2026, 10, 6)),
        ("I spent 100 today", date(2026, 10, 6)),
        ("I spent 100 yesterday", date(2026, 10, 5)),
        ("I spent 100 tomorrow", date(2026, 10, 7)),
        ("I spent 100 the day before yesterday", date(2026, 10, 4)),
        ("I spent 100 the day after tomorrow", date(2026, 10, 8)),
        ("I spent 100 two days ago", date(2026, 10, 4)),
        ("I spent 100 2 days ago", date(2026, 10, 4)),
        ("I spent 100 5 days ago", date(2026, 10, 1)),
        ("I spent 100 10 days back", date(2026, 9, 26)),
        ("I spent 100 in 2 days", date(2026, 10, 8)),
        ("I spent 100 in 5 days", date(2026, 10, 11)),
        ("I spent 100 after 2 days", date(2026, 10, 8)),
        ("I spent 100 2 days from now", date(2026, 10, 8)),
        ("I spent 100 5 days from today", date(2026, 10, 11)),
        ("I spent 100 2 weeks ago", date(2026, 9, 22)),
        ("I spent 100 in 2 weeks", date(2026, 10, 20)),
        ("I spent 100 last week", date(2026, 9, 29)),
        ("I spent 100 next week", date(2026, 10, 13)),
        ("I spent 100 on 06/10/2026", date(2026, 10, 6)),
        ("I spent 100 on 05/10/2026", date(2026, 10, 5)),
        ("I spent 100 on 05-10-2026", date(2026, 10, 5)),
        ("I spent 100 on 2026-10-05", date(2026, 10, 5)),
        ("I spent 100 on 5th October 2026", date(2026, 10, 5)),
        ("I spent 100 on October 5th, 2026", date(2026, 10, 5)),
        ("I spent 100 on 5 October", date(2026, 10, 5)),
        ("I spent 100 on October 5", date(2026, 10, 5)),
        ("I spent 100 on 05/06/2026", date(2026, 6, 5)),
        ("I spent 100 2 days after October 5", date(2026, 10, 7)),
        ("I spent 100 2 days after 2026-10-05", date(2026, 10, 7)),
        ("I spent 100 1 day before 2026-10-10", date(2026, 10, 9)),
    ],
)
def test_resolve_expense_date(message, expected, monkeypatch) -> None:
    received_timezones = []

    def fixed_today(timezone: str) -> date:
        received_timezones.append(timezone)
        return REFERENCE_DATE

    monkeypatch.setattr(dates, "today_in", fixed_today)

    assert dates.resolve_expense_date(message, "Asia/Kolkata") == expected
    assert received_timezones == ["Asia/Kolkata"]


def test_today_in_uses_requested_timezone(monkeypatch) -> None:
    class FixedDateTime:
        @classmethod
        def now(cls, tz=None):
            assert tz == ZoneInfo("Asia/Kolkata")
            return datetime(2026, 10, 6, 0, 30, tzinfo=tz)

    monkeypatch.setattr(dates, "datetime", FixedDateTime)

    assert dates.today_in("Asia/Kolkata") == REFERENCE_DATE


@pytest.mark.parametrize(
    "message",
    [
        "I spent 100 last Friday",
        "I spent 100 at the end of the month",
        "I spent 100 a couple of days ago",
        "I spent 100 0 days ago",
    ],
)
def test_unsupported_or_invalid_relative_dates_are_rejected(message) -> None:
    with pytest.raises(ValueError):
        dates.resolve_expense_date(message, "Asia/Kolkata", today=REFERENCE_DATE)


@pytest.mark.parametrize(
    "message",
    [
        "I spent 100 on 31/02/2025",
        "I spent 100 on 2025-13-01",
        "I spent 100 on 31/02/2025",
    ],
)
def test_invalid_explicit_date_is_rejected(message) -> None:
    with pytest.raises(ValueError, match="Invalid|Malformed"):
        dates.resolve_expense_date(message, "Asia/Kolkata", today=REFERENCE_DATE)


@pytest.mark.parametrize(
    "message",
    [
        "I spent 100 yesterday, actually tomorrow",
        "I spent 100 on 2026-10-05 and 2026-10-06",
    ],
)
def test_conflicting_dates_are_rejected(message) -> None:
    with pytest.raises(ValueError, match="Conflicting"):
        dates.resolve_expense_date(message, "Asia/Kolkata", today=REFERENCE_DATE)


class FakeRegistry:
    def __init__(self):
        self.dispatched = []

    def definitions(self):
        return []

    async def dispatch(self, name, arguments):
        self.dispatched.append((name, dict(arguments)))
        return {"success": True, "expense_date": arguments["expense_date"]}


class FakeAIClient:
    def __init__(self, proposed_date: str):
        self.calls = 0
        self.proposed_date = proposed_date

    async def chat(self, **_kwargs):
        self.calls += 1
        if self.calls == 1:
            return SimpleNamespace(
                content=None,
                tool_calls=[
                    SimpleNamespace(
                        name="add_expense",
                        call_id="call-1",
                        arguments={
                            "amount": 100,
                            "category": "entertainment",
                            "expense_date": self.proposed_date,
                        },
                    )
                ],
            )
        return SimpleNamespace(content="Expense recorded.", tool_calls=[])


async def _run_agent(message: str, history: list[dict[str, str]], monkeypatch):
    from app.agents import orchestrator as orchestrator_module

    monkeypatch.setattr(
        orchestrator_module,
        "get_settings",
        lambda: SimpleNamespace(family_timezone="Asia/Kolkata"),
    )
    monkeypatch.setattr(dates, "today_in", lambda _timezone: REFERENCE_DATE)

    registry = FakeRegistry()
    agent = FamilyContextAgent(FakeAIClient("2025-08-27"), registry)
    state = AgentState(
        family_id=uuid4(),
        user_id=None,
        conversation_id=uuid4(),
        user_message=message,
        history=history,
    )
    result = await agent.run(state)
    return registry, result


@pytest.mark.asyncio
async def test_orchestrator_ignores_incorrect_model_proposed_date(monkeypatch) -> None:
    registry, result = await _run_agent(
        "add 1000 entertainment expense yesterday",
        [{"role": "user", "content": "add 1000 entertainment expense yesterday"}],
        monkeypatch,
    )

    assert registry.dispatched[0][1]["expense_date"] == "2026-10-05"
    assert result.tool_calls[0]["arguments"]["expense_date"] == "2026-10-05"


@pytest.mark.asyncio
async def test_confirmation_uses_original_expense_request_date(monkeypatch) -> None:
    registry, result = await _run_agent(
        "yes",
        [
            {"role": "user", "content": "add 1000 entertainment expense yesterday"},
            {"role": "assistant", "content": "Did you mean yesterday's date?"},
            {"role": "user", "content": "yes"},
        ],
        monkeypatch,
    )

    assert registry.dispatched[0][1]["expense_date"] == "2026-10-05"
    assert result.tool_calls[0]["arguments"]["expense_date"] == "2026-10-05"


@pytest.mark.asyncio
async def test_date_survives_multiple_clarification_turns(monkeypatch) -> None:
    registry, result = await _run_agent(
        "yes",
        [
            {"role": "user", "content": "add 1000 entertainment expense yesterday"},
            {"role": "assistant", "content": "What was the amount?"},
            {"role": "user", "content": "1000"},
            {"role": "assistant", "content": "Did you mean yesterday's date?"},
            {"role": "user", "content": "yes"},
        ],
        monkeypatch,
    )

    assert registry.dispatched[0][1]["expense_date"] == "2026-10-05"
    assert result.tool_calls[0]["arguments"]["expense_date"] == "2026-10-05"
