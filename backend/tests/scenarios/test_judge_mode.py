"""Judge-level journey across the HTTP API, scripted agent, and PostgreSQL."""

from datetime import date
from decimal import Decimal
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import delete, func, select

from app.api.dependencies import get_db, get_today
from app.clients.ai_model import AIResponse, ToolCallRequest
from app.core.constants import CommitmentStatus, CommitmentType, Priority, SourceType
from app.db.session import AsyncSessionLocal
from app.main import app
from app.models.commitment import Commitment
from app.models.commitment_dependency import CommitmentDependency
from app.models.expense import Expense
from app.models.family import Family
from app.models.family_member import FamilyMember

TODAY = date(2026, 10, 13)


class ScriptedJudgeModel:
    """Deterministic action sequence; every request traverses the real agent/tools."""

    def __init__(self):
        self.calls = []
        self.responses = [
            AIResponse(content="The CBC test and student deadline need attention this week.", tool_calls=[]),
            AIResponse(content=None, tool_calls=[ToolCallRequest(
                name="search_commitments", arguments={"title_query": "CBC test"}, call_id="cbc-search",
            )]),
            AIResponse(content=None, tool_calls=[ToolCallRequest(
                name="update_commitment",
                arguments={"commitment_id": "CBC_ID", "status": "COMPLETED"},
                call_id="cbc-complete",
            )]),
            AIResponse(content="The CBC test is completed.", tool_calls=[]),
            AIResponse(content=None, tool_calls=[ToolCallRequest(
                name="add_expense",
                arguments={"amount": "1850", "category": "groceries", "expense_date": TODAY.isoformat()},
                call_id="grocery-expense",
            )]),
            AIResponse(content="Recorded ₹1,850 for groceries.", tool_calls=[]),
        ]

    async def chat(self, *, messages, tools=None, **_kwargs):
        self.calls.append({"messages": messages, "tools": tools})
        return self.responses.pop(0)


async def _db_override():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


def _commitment(family_id, member_id, title, kind, category, due_date):
    return Commitment(
        id=uuid4(), family_id=family_id, member_id=member_id,
        commitment_type=kind, category=category, title=title,
        description=title, amount=None, due_date=due_date,
        status=CommitmentStatus.PENDING.value, priority=Priority.MEDIUM.value,
        source_type=SourceType.MANUAL.value,
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_judge_household_attention_completion_and_expense_journey(monkeypatch):
    import app.services.chat as chat_module
    import app.services.composition as composition_module
    import app.utils.dates as dates_module

    # Keep API date dependencies, chat date resolution, and mutation-triggered
    # priority refreshes on the same deterministic family-local clock.
    monkeypatch.setattr(dates_module, "today_in", _frozen_today)
    monkeypatch.setattr(composition_module, "today_in", _frozen_today)

    family_id, other_family_id = uuid4(), uuid4()
    member_id, other_member_id = uuid4(), uuid4()
    cbc = _commitment(family_id, member_id, "CBC test", CommitmentType.LAB_TEST.value, "MEDICAL", date(2026, 10, 14))
    doctor = _commitment(family_id, member_id, "Doctor Review", CommitmentType.APPOINTMENT.value, "MEDICAL", date(2026, 10, 18))
    student = _commitment(family_id, member_id, "Student registration deadline", CommitmentType.DEADLINE.value, "EDUCATION", date(2026, 10, 16))
    electricity = _commitment(family_id, member_id, "KSEB Electricity Bill", CommitmentType.BILL.value, "ELECTRICITY", date(2026, 10, 18))
    unrelated = _commitment(other_family_id, other_member_id, "Private other-family deadline", CommitmentType.TASK.value, "HOME", date(2026, 10, 15))
    model = ScriptedJudgeModel()
    model.responses[2] = AIResponse(content=None, tool_calls=[ToolCallRequest(
        name="update_commitment",
        arguments={"commitment_id": str(cbc.id), "status": "COMPLETED"},
        call_id="cbc-complete",
    )])
    monkeypatch.setattr(chat_module, "AIModelClient", lambda: model)
    previous_overrides = dict(app.dependency_overrides)
    app.dependency_overrides[get_db] = _db_override
    app.dependency_overrides[get_today] = _async_today

    async with AsyncSessionLocal() as session:
        session.add_all([
            Family(id=family_id, name="Nair Judge Scenario"),
            Family(id=other_family_id, name="Unrelated Household"),
            FamilyMember(id=member_id, family_id=family_id, name="Anil Nair", relationship_type="PARENT"),
            FamilyMember(id=other_member_id, family_id=other_family_id, name="Other Member", relationship_type="PARENT"),
            cbc, doctor, student, electricity, unrelated,
            Expense(family_id=family_id, member_id=member_id, amount=Decimal("1200.00"), category="GROCERIES", expense_date=TODAY, source_type=SourceType.MANUAL.value),
            CommitmentDependency(
                id=uuid4(), family_id=family_id,
                source_commitment_id=cbc.id, target_commitment_id=doctor.id,
                relationship_type="MUST_COMPLETE_BEFORE",
            ),
        ])
        await session.commit()

    expected = {"isolated": False, "attention_context": False, "completion": False,
                "single_expense": False, "api_db_agree": False}
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            initial_priorities = await client.post(
                "/api/v1/priorities/recalculate", params={"family_id": str(family_id)},
            )
            attention = await client.post("/api/v1/chat", json={
                "family_id": str(family_id), "member_id": str(member_id),
                "message": "What needs my attention this week?",
            })
            completion = await client.post("/api/v1/chat", json={
                "family_id": str(family_id), "member_id": str(member_id),
                "message": "The CBC is done.",
            })
            expense_response = await client.post("/api/v1/chat", json={
                "family_id": str(family_id), "member_id": str(member_id),
                "message": "I spent ₹1,850 on groceries.",
            })
            commitments_response = await client.get(
                "/api/v1/commitments", params={"family_id": str(family_id)},
            )
            expenses_response = await client.get(
                "/api/v1/expenses", params={"family_id": str(family_id)},
            )
            priorities_after = await client.get(
                "/api/v1/priorities", params={"family_id": str(family_id)},
            )

        prompt = model.calls[0]["messages"][0]["content"]
        expense_rows = list((await session.scalars(
            select(Expense).where(Expense.family_id == family_id)
        )).all())
        commitment_rows = list((await session.scalars(
            select(Commitment).where(Commitment.family_id == family_id)
        )).all())
        persisted_cbc = await session.scalar(select(Commitment).where(Commitment.id == cbc.id))

        expected["isolated"] = (
            "Nair Judge Scenario" in prompt
            and "Private other-family deadline" not in prompt
            and all(item["family_id"] == str(family_id) for item in commitments_response.json())
        )
        expected["attention_context"] = (
            initial_priorities.status_code == 200
            and all(term in prompt for term in ("CBC test", "Doctor Review", "Student registration deadline", "KSEB Electricity Bill"))
            and "unrelated" not in attention.json()["message"].lower()
        )
        expected["completion"] = (
            completion.status_code == 200
            and persisted_cbc.status == CommitmentStatus.COMPLETED.value
            and persisted_cbc.completed_at is not None
            and len(commitment_rows) == 4
        )
        expected["single_expense"] = (
            expense_response.status_code == 200
            and len(expense_rows) == 2
            and sum(row.amount == Decimal("1850.00") for row in expense_rows) == 1
            and any(row.category == "GROCERIES" and row.expense_date == TODAY for row in expense_rows if row.amount == Decimal("1850.00"))
        )
        expected["api_db_agree"] = (
            expenses_response.status_code == 200
            and any(Decimal(str(item["amount"])) == Decimal("1850.00") and item["category"] == "GROCERIES" for item in expenses_response.json())
            and priorities_after.status_code == 200
        )
        assert expected == {key: True for key in expected}, expected
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)
        async with AsyncSessionLocal() as cleanup:
            await cleanup.rollback()
            await cleanup.execute(delete(Family).where(Family.id.in_([family_id, other_family_id])))
            await cleanup.commit()


def _frozen_today(_timezone=None):
    return TODAY


async def _async_today():
    return _frozen_today()
