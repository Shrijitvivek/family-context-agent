"""Scripted decision/tool-cycle tests backed by the real PostgreSQL registry."""

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import delete, func, select

from app.agents.state import AgentState
from app.clients.ai_model import AIResponse, ToolCallRequest
from app.core.constants import CommitmentStatus, CommitmentType, Priority, SourceType
from app.db.session import AsyncSessionLocal
from app.models.commitment import Commitment
from app.models.expense import Expense
from app.models.family import Family
from app.models.family_member import FamilyMember
from app.services.chat import ChatService


TODAY = date(2026, 10, 13)


class ScriptedDecisionModel:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    async def chat(self, *, messages, tools=None, **_kwargs):
        self.calls.append({"messages": messages, "tools": tools})
        assert self.responses, "script has no response for this model turn"
        return self.responses.pop(0)


def _tool(name, arguments, call_id=None):
    return AIResponse(content=None, tool_calls=[ToolCallRequest(
        name=name, arguments=arguments, call_id=call_id or name,
    )])


def _plain(text):
    return AIResponse(content=text, tool_calls=[])


def _bill(family_id, member_id, title, due_date, *, status="PENDING", category="ELECTRICITY"):
    return Commitment(
        id=uuid4(), family_id=family_id, member_id=member_id,
        commitment_type=CommitmentType.BILL.value, category=category,
        title=title, description=title, amount=Decimal("3240.00"),
        due_date=due_date, status=status, priority=Priority.MEDIUM.value,
        source_type=SourceType.MANUAL.value,
    )


async def _cleanup(session, family_id):
    await session.rollback()
    await session.execute(delete(Family).where(Family.id == family_id))
    await session.commit()


def _install_model(monkeypatch, model):
    import app.services.chat as chat_module
    from app.utils import dates
    from types import SimpleNamespace
    from app.agents import orchestrator

    monkeypatch.setattr(chat_module, "AIModelClient", lambda: model)
    monkeypatch.setattr(dates, "today_in", lambda _timezone: TODAY)
    monkeypatch.setattr(orchestrator, "get_settings", lambda: SimpleNamespace(family_timezone="Asia/Kolkata"))


async def _seed_family(session, family_id, member_id):
    session.add_all([
        Family(id=family_id, name="Decision Test Family"),
        FamilyMember(id=member_id, family_id=family_id, name="Rahul", relationship_type="PARENT"),
    ])
    await session.flush()


@pytest.mark.asyncio(loop_scope="session")
async def test_agent_routes_expense_and_bill_to_different_real_tools(monkeypatch):
    family_id, member_id = uuid4(), uuid4()
    model = ScriptedDecisionModel([
        _tool("add_expense", {"amount": "1850", "category": "groceries"}),
        _plain("Recorded ₹1,850 groceries."),
        _tool("create_commitment", {
            "commitment_type": "BILL", "category": "ELECTRICITY",
            "title": "Electricity Bill", "amount": "3240", "due_date": "2026-10-18",
        }),
        _plain("Added the electricity bill."),
    ])
    _install_model(monkeypatch, model)
    async with AsyncSessionLocal() as session:
        await _seed_family(session, family_id, member_id)
        try:
            service = ChatService(session)
            expense_result = await service.process_message(
                family_id=family_id, member_id=member_id, conversation_id=None,
                message="I spent ₹1,850 on groceries today.",
            )
            assert await session.scalar(
                select(func.count(Commitment.id)).where(Commitment.family_id == family_id)
            ) == 0
            bill_result = await service.process_message(
                family_id=family_id, member_id=member_id, conversation_id=None,
                message="Electricity bill ₹3,240 is due October 18.",
            )
            expenses = list((await session.scalars(select(Expense).where(Expense.family_id == family_id))).all())
            commitments = list((await session.scalars(select(Commitment).where(Commitment.family_id == family_id))).all())
            assert [call["name"] for call in expense_result.tool_calls] == ["add_expense"]
            assert [call["name"] for call in bill_result.tool_calls] == ["create_commitment"]
            assert expenses[0].amount == Decimal("1850.00")
            assert expenses[0].category == "GROCERIES"
            assert expenses[0].expense_date == TODAY
            assert expenses[0].member_id == member_id
            assert len(commitments) == 1
            assert commitments[0].title == "Electricity Bill"
            assert commitments[0].commitment_type == "BILL"
            assert commitments[0].amount == Decimal("3240.00")
            assert commitments[0].due_date == date(2026, 10, 18)
            assert commitments[0].member_id == member_id
            assert len(expenses) == 1
        finally:
            await _cleanup(session, family_id)


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize(
    ("user_message", "arguments", "expected_missing"),
    [
        ("Add an expense for groceries.", {"category": "groceries"}, "amount"),
        ("I paid ₹500.", {"amount": "500"}, "category"),
    ],
)
async def test_agent_tool_validation_prevents_expense_without_required_field(
    monkeypatch, user_message, arguments, expected_missing,
):
    family_id, member_id = uuid4(), uuid4()
    model = ScriptedDecisionModel([
        _tool("add_expense", arguments),
        _plain(f"What was the {expected_missing} for this expense?"),
    ])
    _install_model(monkeypatch, model)
    async with AsyncSessionLocal() as session:
        await _seed_family(session, family_id, member_id)
        try:
            result = await ChatService(session).process_message(
                family_id=family_id, member_id=member_id, conversation_id=None, message=user_message,
            )
            rows = list((await session.scalars(select(Expense).where(Expense.family_id == family_id))).all())
            assert len(result.tool_calls) == 1
            assert result.tool_results[0]["result"]["success"] is False
            assert "expense" in result.assistant_message.casefold()
            assert rows == []
        finally:
            await _cleanup(session, family_id)


@pytest.mark.asyncio(loop_scope="session")
async def test_agent_updates_existing_commitment_for_completion_and_reschedule(monkeypatch):
    family_id, member_id = uuid4(), uuid4()
    electricity = _bill(family_id, member_id, "Electricity Bill", date(2026, 10, 18))
    internet = _bill(family_id, member_id, "Internet Bill", date(2026, 10, 20), category="INTERNET")
    model = ScriptedDecisionModel([
        _tool("search_commitments", {"title_query": "electricity bill"}, "search-elec"),
        _tool("update_commitment", {"commitment_id": str(electricity.id), "status": "COMPLETED"}, "complete-elec"),
        _plain("Marked the existing electricity bill completed."),
        _tool("search_commitments", {"title_query": "internet bill"}, "search-internet"),
        _tool("update_commitment", {"commitment_id": str(internet.id), "due_date": "2026-10-25"}, "move-internet"),
        _plain("Moved the existing internet bill to October 25."),
    ])
    _install_model(monkeypatch, model)
    async with AsyncSessionLocal() as session:
        await _seed_family(session, family_id, member_id)
        session.add_all([electricity, internet])
        await session.flush()
        try:
            service = ChatService(session)
            complete = await service.process_message(
                family_id=family_id, member_id=member_id, conversation_id=None,
                message="I paid the electricity bill.",
            )
            reschedule = await service.process_message(
                family_id=family_id, member_id=member_id, conversation_id=None,
                message="Move the internet bill to October 25.",
            )
            await session.refresh(electricity)
            await session.refresh(internet)
            rows = list((await session.scalars(select(Commitment).where(Commitment.family_id == family_id))).all())
            assert [call["name"] for call in complete.tool_calls] == ["search_commitments", "update_commitment"]
            assert complete.tool_calls[1]["arguments"]["commitment_id"] == str(electricity.id)
            assert electricity.status == CommitmentStatus.COMPLETED.value
            assert [call["name"] for call in reschedule.tool_calls] == ["search_commitments", "update_commitment"]
            assert reschedule.tool_calls[1]["arguments"]["commitment_id"] == str(internet.id)
            assert reschedule.tool_calls[1]["arguments"]["due_date"] == "2026-10-25"
            assert internet.due_date == date(2026, 10, 25)
            assert len(rows) == 2
        finally:
            await _cleanup(session, family_id)


@pytest.mark.asyncio(loop_scope="session")
async def test_agent_does_not_reopen_or_duplicate_already_completed_commitment(monkeypatch):
    family_id, member_id = uuid4(), uuid4()
    completed = _bill(family_id, member_id, "Electricity Bill", date(2026, 10, 18), status="COMPLETED")
    model = ScriptedDecisionModel([
        _tool("search_commitments", {"title_query": "electricity bill", "status": "COMPLETED"}, "search"),
        _tool("update_commitment", {"commitment_id": str(completed.id), "status": "COMPLETED"}, "idempotent-complete"),
        _plain("That electricity bill is already completed."),
    ])
    _install_model(monkeypatch, model)
    async with AsyncSessionLocal() as session:
        await _seed_family(session, family_id, member_id)
        session.add(completed)
        await session.flush()
        try:
            result = await ChatService(session).process_message(
                family_id=family_id, member_id=member_id, conversation_id=None,
                message="Mark the electricity bill as completed.",
            )
            await session.refresh(completed)
            assert [call["name"] for call in result.tool_calls] == ["search_commitments", "update_commitment"]
            assert result.tool_results[1]["result"]["success"] is True
            assert completed.status == CommitmentStatus.COMPLETED.value
            assert await session.scalar(select(func.count(Commitment.id)).where(Commitment.family_id == family_id)) == 1
        finally:
            await _cleanup(session, family_id)


@pytest.mark.asyncio(loop_scope="session")
async def test_unsupported_request_does_not_dispatch_a_tool(monkeypatch):
    family_id, member_id = uuid4(), uuid4()
    model = ScriptedDecisionModel([_plain("I can't make bank transfers. This app does not support payments.")])
    _install_model(monkeypatch, model)
    async with AsyncSessionLocal() as session:
        await _seed_family(session, family_id, member_id)
        try:
            result = await ChatService(session).process_message(
                family_id=family_id, member_id=member_id, conversation_id=None,
                message="Transfer ₹10,000 to my landlord's bank account.",
            )
            assert result.tool_calls == []
            assert "does not support" in result.assistant_message
            assert await session.scalar(select(func.count(Expense.id)).where(Expense.family_id == family_id)) == 0
            assert await session.scalar(select(func.count(Commitment.id)).where(Commitment.family_id == family_id)) == 0
        finally:
            await _cleanup(session, family_id)


@pytest.mark.asyncio(loop_scope="session")
async def test_duplicate_bill_attempt_is_rejected_without_creating_another_row(monkeypatch):
    family_id, member_id = uuid4(), uuid4()
    existing = _bill(family_id, member_id, "Electricity Bill", date(2026, 10, 18))
    create_arguments = {
        "commitment_type": "BILL", "category": "ELECTRICITY",
        "title": "Electricity Bill", "amount": "3240.00", "due_date": "2026-10-18",
    }
    model = ScriptedDecisionModel([
        _tool("create_commitment", create_arguments, "duplicate-attempt"),
        _plain("A matching electricity bill already exists. Is this the same bill?"),
    ])
    _install_model(monkeypatch, model)
    async with AsyncSessionLocal() as session:
        await _seed_family(session, family_id, member_id)
        session.add(existing)
        await session.flush()
        try:
            result = await ChatService(session).process_message(
                family_id=family_id, member_id=member_id, conversation_id=None,
                message="Electricity bill ₹3,240 is due October 18.",
            )
            rows = list((await session.scalars(select(Commitment).where(Commitment.family_id == family_id))).all())
            assert result.tool_results[0]["result"]["success"] is False
            assert "already exists" in result.assistant_message
            assert len(rows) == 1
            assert rows[0].id == existing.id
        finally:
            await _cleanup(session, family_id)


@pytest.mark.asyncio(loop_scope="session")
async def test_agent_blocks_unrequested_tool_when_update_cannot_be_verified(monkeypatch):
    family_id, member_id = uuid4(), uuid4()
    existing = _bill(family_id, member_id, "Internet Bill", date(2026, 10, 20), category="INTERNET")
    model = ScriptedDecisionModel([
        AIResponse(content=None, tool_calls=[
            ToolCallRequest(
                name="update_commitment",
                arguments={"commitment_id": str(uuid4()), "due_date": "2026-10-25"},
                call_id="missing-update-target",
            ),
            ToolCallRequest(
                name="add_expense",
                arguments={"amount": "45.00", "category": "FOOD"},
                call_id="unrequested-expense",
            ),
        ]),
        _plain("I couldn't move the internet bill."),
    ])
    _install_model(monkeypatch, model)
    async with AsyncSessionLocal() as session:
        await _seed_family(session, family_id, member_id)
        session.add(existing)
        await session.flush()
        try:
            result = await ChatService(session).process_message(
                family_id=family_id, member_id=member_id, conversation_id=None,
                message="Move the internet bill to October 25.",
            )
            expenses = list((await session.scalars(select(Expense).where(Expense.family_id == family_id))).all())
            await session.refresh(existing)
            assert [call["name"] for call in result.tool_calls] == ["search_commitments"]
            assert result.requires_clarification is True
            assert len(expenses) == 0
            assert existing.due_date == date(2026, 10, 20)
        finally:
            await _cleanup(session, family_id)
