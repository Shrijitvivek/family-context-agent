from datetime import date
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.agents.state import AgentState
from app.schemas.demo import Scenario
from app.services.chat import ChatService
from app.services.dependency import would_create_cycle
from app.services.document import parse_extracted_fields


class FakeConversations:
    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []

    async def create(self, family_id):
        return SimpleNamespace(id=uuid4(), family_id=family_id)

    async def get(self, family_id, conversation_id):
        return SimpleNamespace(id=conversation_id, family_id=family_id)

    async def recent_messages(self, conversation_id, limit):
        return []

    async def add_message(self, *, conversation_id, role, content):
        self.messages.append((role, content))


class FakeAgent:
    async def run(self, state: AgentState) -> AgentState:
        state.assistant_message = "I recorded the expense."
        state.tool_calls.append({"name": "add_expense", "arguments": {"amount": 500}})
        return state


class FakeEvents:
    def __init__(self) -> None:
        self.events: list[dict] = []
        self.commits = 0

    async def add(self, **event) -> None:
        self.events.append(event)

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        raise AssertionError("successful chat must not roll back")


@pytest.mark.asyncio
async def test_chat_service_process_message_persists_messages_and_agent_run_event() -> None:
    service = ChatService.__new__(ChatService)
    conversations = FakeConversations()
    events = FakeEvents()
    service._conversation_repository = conversations
    service._document_repository = SimpleNamespace()
    service._context_service = SimpleNamespace(
        build=lambda **_kwargs: _empty_async_result(None)
    )
    service._agent = FakeAgent()
    service._event_repository = events

    state = await service.process_message(
        family_id=uuid4(), user_id=None, conversation_id=None, message="Spent 500 on food"
    )

    assert state.assistant_message == "I recorded the expense."
    assert [role for role, _ in conversations.messages] == ["user", "assistant"]
    assert events.events[0]["event_type"] == "agent_run"
    assert events.events[0]["event_data"]["tool_calls"] == state.tool_calls
    assert events.commits == 1


async def _empty_async_result(value):
    return value


def test_extraction_keeps_valid_fields_and_reports_invalid_ones() -> None:
    fields = parse_extracted_fields(
        {
            "commitment_type": "BILL",
            "title": "KSEB Electricity Bill",
            "amount": "not a number",
            "due_date": "2026-10-18",
            "unexpected_key": "ignored",
            "missing_fields": ["member_name"],
        }
    )

    assert fields.title == "KSEB Electricity Bill"
    assert fields.amount is None
    assert fields.due_date == date(2026, 10, 18)
    assert fields.missing_fields == ["amount", "member_name"]


def test_dependency_cycle_detection() -> None:
    a, b, c = uuid4(), uuid4(), uuid4()
    assert would_create_cycle([(a, b), (b, c)], c, a)
    assert not would_create_cycle([(a, b), (b, c)], a, c)


def test_bundled_demo_scenarios_are_valid_and_consistent() -> None:
    scenario_dir = Path(__file__).resolve().parents[3] / "synthetic_data" / "scenarios"
    files = list(scenario_dir.glob("*.json"))
    assert files, "expected at least one demo scenario"
    for path in files:
        scenario = Scenario.model_validate_json(path.read_text(encoding="utf-8"))
        member_keys = {member.key for member in scenario.members}
        commitment_keys = {commitment.key for commitment in scenario.commitments}
        assert {commitment.member for commitment in scenario.commitments} - {None} <= member_keys
        assert {expense.member for expense in scenario.expenses} - {None} <= member_keys
        for dependency in scenario.dependencies:
            assert {dependency.source, dependency.target} <= commitment_keys
