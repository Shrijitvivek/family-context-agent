from datetime import date
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.agents.orchestrator import FamilyContextAgent, _expense_date_from_request
from app.agents.state import AgentState


TODAY = date(2026, 10, 1)


@pytest.mark.parametrize(
    ("user_text", "expected"),
    [
        ("I spent 500 today", date(2026, 10, 1)),
        ("I spent 500 yesterday", date(2026, 9, 30)),
        ("I spent 500 tomorrow", date(2026, 10, 2)),
        ("I spent 500 on 02/10/2026", date(2026, 10, 2)),
        ("I spent 500 on 2026-09-30", date(2026, 9, 30)),
        ("I spent 500 this month", date(2026, 10, 1)),
        ("I spent 500", date(2026, 10, 1)),
    ],
)
def test_expense_date_comes_from_request(user_text: str, expected: date) -> None:
    assert _expense_date_from_request(user_text, TODAY) == expected


@pytest.mark.asyncio
async def test_agent_supplies_family_date_and_ignores_model_date(monkeypatch) -> None:
    import app.agents.orchestrator as orchestrator_module

    monkeypatch.setattr(orchestrator_module, "today_in", lambda _: TODAY)
    monkeypatch.setattr(
        orchestrator_module,
        "get_settings",
        lambda: SimpleNamespace(family_timezone="Asia/Kolkata"),
    )

    class FakeAI:
        async def chat(self, *, messages, tools):
            assert "Current date in the family timezone (Asia/Kolkata): 2026-10-01" in messages[0]["content"]
            return SimpleNamespace(
                tool_calls=[SimpleNamespace(
                    call_id="call-1",
                    name="add_expense",
                    arguments={"amount": 500, "category": "groceries", "expense_date": "2025-08-15"},
                )],
                content=None,
            )

    class FakeRegistry:
        def __init__(self):
            self.arguments = None

        def definitions(self):
            return []

        async def dispatch(self, name, arguments):
            self.arguments = arguments
            return {"success": True}

    registry = FakeRegistry()
    agent = FamilyContextAgent(FakeAI(), registry)
    state = AgentState(
        family_id=uuid4(), user_id=None, conversation_id=None,
        user_message="I spent 500 on groceries today",
    )

    await agent.run(state)

    assert registry.arguments["expense_date"] == "2026-10-01"

