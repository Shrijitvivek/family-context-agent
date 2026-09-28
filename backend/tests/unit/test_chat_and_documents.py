"""Chat workflow, document extraction, and demo scenario unit tests (no database)."""

from datetime import date
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from app.agents.orchestrator import FamilyContextOrchestrator
from app.core.exceptions import AIModelError
from app.schemas.agent import AgentDecision
from app.schemas.chat import ChatRequest
from app.schemas.demo import Scenario
from app.services.chat import ChatService, describe_tool_result
from app.services.dependency import would_create_cycle
from app.services.document import parse_extracted_fields

TODAY = date(2026, 10, 10)


class FakeConversations:
    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []
        self.commits = 0

    async def create(self, family_id):
        return SimpleNamespace(id=uuid4(), family_id=family_id)

    async def get(self, family_id, conversation_id):
        return SimpleNamespace(id=conversation_id, family_id=family_id)

    async def recent_messages(self, conversation_id, limit):
        return []

    async def add_message(self, conversation_id, role, content):
        self.messages.append((role, content))

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        pass


class FakeContext:
    async def build(self, family_id, member_id=None):
        return SimpleNamespace(to_prompt=lambda: "Household: Nair Family")


class FakeRegistry:
    names = ("add_expense",)

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def definitions(self):
        return []

    async def dispatch(self, name, arguments):
        self.calls.append(arguments)
        return {"success": True, "expense_id": str(uuid4()), "message": "Expense recorded"}


class FakeModel:
    def __init__(self, decision: AgentDecision | Exception) -> None:
        self.decision = decision
        self.messages: list[dict] = []

    async def decide(self, messages, tools):
        self.messages = messages
        if isinstance(self.decision, Exception):
            raise self.decision
        return self.decision


def make_service(model: FakeModel):
    conversations, registry = FakeConversations(), FakeRegistry()
    service = ChatService(
        conversations=conversations,  # type: ignore[arg-type]
        context=FakeContext(),  # type: ignore[arg-type]
        orchestrator=FamilyContextOrchestrator(registry),
        model=model,  # type: ignore[arg-type]
        today=lambda: TODAY,
    )
    return service, conversations, registry


@pytest.mark.asyncio
async def test_chat_executes_tool_and_confirms_from_real_arguments() -> None:
    family_id = uuid4()
    model = FakeModel(
        AgentDecision.tool(
            "add_expense",
            {"amount": "500", "category": "groceries", "expense_date": "2026-10-10",
             "family_id": str(uuid4())},  # a model-supplied family id must be ignored
        )
    )
    service, conversations, registry = make_service(model)

    response = await service.handle(ChatRequest(family_id=family_id, message="Spent 500 on veg"))

    assert response.action == "tool_call"
    assert response.reply == "Recorded ₹500 for groceries on 2026-10-10."
    assert registry.calls[0]["family_id"] == str(family_id)
    assert [role for role, _ in conversations.messages] == ["user", "assistant"]
    assert model.messages[1] == {"role": "system", "content": "Household: Nair Family"}


@pytest.mark.asyncio
async def test_chat_asks_for_missing_fields_without_calling_tool() -> None:
    service, _, registry = make_service(
        FakeModel(AgentDecision.tool("add_expense", {"amount": "500"}))
    )
    response = await service.handle(ChatRequest(family_id=uuid4(), message="I spent 500"))

    assert response.action == "clarification"
    assert "category" in response.missing_fields
    assert registry.calls == []


@pytest.mark.asyncio
async def test_chat_model_outage_is_saved_and_reported_honestly() -> None:
    service, conversations, _ = make_service(FakeModel(AIModelError("down")))
    response = await service.handle(ChatRequest(family_id=uuid4(), message="hello"))

    assert response.action == "error"
    assert "Nothing was changed" in response.reply
    assert conversations.messages[0] == ("user", "hello")
    assert conversations.commits == 2  # user message committed before the model call


def test_describe_summary_and_empty_search() -> None:
    summary = describe_tool_result(
        "get_expense_summary",
        {},
        {"total": "3050.00", "transaction_count": 2, "category": "GROCERIES"},
    )
    assert summary == "You spent ₹3050.00 on GROCERIES across 2 transaction(s)."
    assert "couldn't find" in describe_tool_result("search_commitments", {}, {"commitments": []})
    priorities = describe_tool_result(
        "get_family_priorities", {}, {"items": [{"message": "Water bill is due today."}]}
    )
    assert priorities == "- Water bill is due today."


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
        member_keys = {m.key for m in scenario.members}
        commitment_keys = {c.key for c in scenario.commitments}
        assert {c.member for c in scenario.commitments} - {None} <= member_keys
        assert {e.member for e in scenario.expenses} - {None} <= member_keys
        for d in scenario.dependencies:
            assert {d.source, d.target} <= commitment_keys
