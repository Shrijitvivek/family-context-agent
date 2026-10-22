
"""HTTP boundary checks for family/member scoping against PostgreSQL."""

from datetime import date
from decimal import Decimal
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import delete, func, select

from app.api.dependencies import get_db
from app.clients.ai_model import AIResponse
from app.core.constants import CommitmentStatus, CommitmentType, Priority, SourceType
from app.db.session import AsyncSessionLocal
from app.main import app
from app.models.commitment import Commitment
from app.models.document import Document
from app.models.expense import Expense
from app.models.family import Family
from app.models.family_member import FamilyMember
from app.models.notification import Notification


class ScriptedAPIChatModel:
    def __init__(self):
        self.calls = []

    async def chat(self, *, messages, tools=None, **_kwargs):
        self.calls.append(messages)
        return AIResponse(content="I can help with your household.", tool_calls=[])


async def _db_override():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def _cleanup(session, family_ids):
    await session.rollback()
    await session.execute(delete(Family).where(Family.id.in_(family_ids)))
    await session.commit()


def _commitment(family_id, member_id, title, due_date):
    return Commitment(
        id=uuid4(),
        family_id=family_id,
        member_id=member_id,
        commitment_type=CommitmentType.BILL.value,
        category="ELECTRICITY",
        title=title,
        description=title,
        amount=Decimal("3240.00"),
        due_date=due_date,
        status=CommitmentStatus.PENDING.value,
        priority=Priority.MEDIUM.value,
        source_type=SourceType.MANUAL.value,
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_read_endpoints_scope_commitments_expenses_documents_priorities_and_timeline():
    family_a, family_b = uuid4(), uuid4()
    member_a, member_b = uuid4(), uuid4()
    commitment_a = _commitment(
        family_a, member_a, "A Electricity Bill", date(2026, 10, 15)
    )
    commitment_b = _commitment(
        family_b, member_b, "B Private Electricity Bill", date(2026, 10, 15)
    )
    expense_a_id, expense_b_id = uuid4(), uuid4()
    document_a_id, document_b_id = uuid4(), uuid4()
    previous_overrides = dict(app.dependency_overrides)
    app.dependency_overrides[get_db] = _db_override

    async with AsyncSessionLocal() as session:
        session.add_all(
            [
                Family(id=family_a, name="Family Alpha"),
                Family(id=family_b, name="Family Beta"),
                FamilyMember(
                    id=member_a,
                    family_id=family_a,
                    name="Alice",
                    relationship_type="PARENT",
                ),
                FamilyMember(
                    id=member_b,
                    family_id=family_b,
                    name="Bob Secret",
                    relationship_type="PARENT",
                ),
                commitment_a,
                commitment_b,
                Expense(
                    id=expense_a_id,
                    family_id=family_a,
                    member_id=member_a,
                    amount=Decimal("55.00"),
                    category="GROCERIES",
                    expense_date=date(2026, 10, 13),
                    source_type=SourceType.MANUAL.value,
                ),
                Expense(
                    id=expense_b_id,
                    family_id=family_b,
                    member_id=member_b,
                    amount=Decimal("999.00"),
                    category="PRIVATE",
                    expense_date=date(2026, 10, 13),
                    source_type=SourceType.MANUAL.value,
                ),
                Document(
                    id=document_a_id,
                    family_id=family_a,
                    uploaded_by_member_id=member_a,
                    file_name="alpha.pdf",
                    file_path="alpha.pdf",
                    mime_type="application/pdf",
                    processing_status="NEEDS_CONFIRMATION",
                ),
                Document(
                    id=document_b_id,
                    family_id=family_b,
                    uploaded_by_member_id=member_b,
                    file_name="secret-beta.pdf",
                    file_path="secret-beta.pdf",
                    mime_type="application/pdf",
                    processing_status="NEEDS_CONFIRMATION",
                ),
            ]
        )
        await session.flush()
        await session.commit()

        try:
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                # Valid family/member responses and ordinary family data.
                family_response = await client.get(
                    f"/api/v1/families/{family_a}"
                )
                members_response = await client.get(
                    f"/api/v1/families/{family_a}/members"
                )
                assert family_response.status_code == members_response.status_code == 200
                assert family_response.json()["name"] == "Family Alpha"
                assert [m["id"] for m in members_response.json()] == [str(member_a)]
                assert "Bob Secret" not in family_response.text + members_response.text

                commitments = await client.get(
                    "/api/v1/commitments",
                    params={"family_id": str(family_a)},
                )
                expenses = await client.get(
                    "/api/v1/expenses",
                    params={"family_id": str(family_a)},
                )
                documents = await client.get(
                    "/api/v1/documents",
                    params={"family_id": str(family_a)},
                )
                foreign_member_documents = await client.get(
                    "/api/v1/documents",
                    params={
                        "family_id": str(family_a),
                        "member_id": str(member_b),
                    },
                )

                assert (
                    commitments.status_code
                    == expenses.status_code
                    == documents.status_code
                    == 200
                )

                # A foreign member filter currently returns an empty list.
                assert foreign_member_documents.status_code == 200
                assert foreign_member_documents.json() == []

                assert [item["id"] for item in commitments.json()] == [
                    str(commitment_a.id)
                ]
                assert [item["id"] for item in expenses.json()] == [
                    str(expense_a_id)
                ]
                assert [item["id"] for item in documents.json()] == [
                    str(document_a_id)
                ]

                serialized = commitments.text + expenses.text + documents.text
                assert str(commitment_b.id) not in serialized
                assert str(expense_b_id) not in serialized
                assert str(document_b_id) not in serialized
                assert "Bob Secret" not in serialized
                assert "secret-beta.pdf" not in serialized

                # Foreign resource IDs must not expose another family's records.
                foreign_gets = [
                    await client.get(
                        f"/api/v1/commitments/{commitment_b.id}",
                        params={"family_id": str(family_a)},
                    ),
                    await client.get(
                        f"/api/v1/documents/{document_b_id}",
                        params={"family_id": str(family_a)},
                    ),
                    await client.post(
                        f"/api/v1/documents/{document_b_id}/process",
                        params={"family_id": str(family_a)},
                    ),
                    await client.post(
                        f"/api/v1/documents/{document_b_id}/confirm",
                        json={
                            "family_id": str(family_a),
                            "commitment_type": "BILL",
                            "title": "Wrong family bill",
                            "due_date": "2026-10-20",
                        },
                    ),
                ]

                assert all(
                    response.status_code == 404 for response in foreign_gets
                )
                assert all(
                    response.json()["code"] == "not_found"
                    for response in foreign_gets
                )
                assert "secret-beta.pdf" not in " ".join(
                    response.text for response in foreign_gets
                )

                # Cross-family PATCH must not modify the other family's record.
                patch_response = await client.patch(
                    f"/api/v1/commitments/{commitment_b.id}",
                    json={
                        "family_id": str(family_a),
                        "status": "COMPLETED",
                    },
                )
                assert patch_response.status_code == 404
                assert patch_response.json()["code"] == "not_found"

                foreign_member_patch = await client.patch(
                    f"/api/v1/families/{family_a}/members/{member_b}",
                    json={"name": "Should not be renamed"},
                )
                assert foreign_member_patch.status_code == 404
                assert foreign_member_patch.json()["code"] == "not_found"

                # Recalculate and verify family-scoped priorities and timeline.
                recalc = await client.post(
                    "/api/v1/priorities/recalculate",
                    params={"family_id": str(family_a)},
                )
                priorities = await client.get(
                    "/api/v1/priorities",
                    params={"family_id": str(family_a)},
                )
                timeline = await client.get(
                    "/api/v1/timeline",
                    params={"family_id": str(family_a)},
                )

                assert (
                    recalc.status_code
                    == priorities.status_code
                    == timeline.status_code
                    == 200
                )
                assert all(
                    item["commitment"]["family_id"] == str(family_a)
                    for item in priorities.json()
                )

                timeline_rows = [
                    commitment
                    for day in timeline.json()["days"]
                    for commitment in day["commitments"]
                ]
                assert [item["id"] for item in timeline_rows] == [
                    str(commitment_a.id)
                ]
                assert all(
                    item["family_id"] == str(family_a)
                    for item in timeline_rows
                )

                # Missing records return 404 Not Found.
                missing_id = uuid4()
                missing_family = await client.get(
                    f"/api/v1/families/{missing_id}"
                )
                missing_expenses = await client.get(
                    "/api/v1/expenses",
                    params={"family_id": str(missing_id)},
                )
                missing_priorities = await client.get(
                    "/api/v1/priorities",
                    params={"family_id": str(missing_id)},
                )
                missing_timeline = await client.get(
                    "/api/v1/timeline",
                    params={"family_id": str(missing_id)},
                )

                missing_responses = (
                    missing_family,
                    missing_expenses,
                    missing_priorities,
                    missing_timeline,
                )
                assert all(
                    response.status_code == 404
                    for response in missing_responses
                )
                assert all(
                    response.json()["code"] == "not_found"
                    for response in missing_responses
                )

            await session.refresh(commitment_b)
            assert commitment_b.status == CommitmentStatus.PENDING.value
            assert (
                await session.scalar(
                    select(func.count(Expense.id)).where(
                        Expense.id == expense_b_id
                    )
                )
                == 1
            )
            assert (
                await session.scalar(
                    select(func.count(Document.id)).where(
                        Document.id == document_b_id
                    )
                )
                == 1
            )

        finally:
            await _cleanup(session, [family_a, family_b])
            app.dependency_overrides.clear()
            app.dependency_overrides.update(previous_overrides)


@pytest.mark.asyncio(loop_scope="session")
async def test_write_endpoints_reject_foreign_member_and_leave_database_unchanged():
    family_a, family_b = uuid4(), uuid4()
    member_a, member_b = uuid4(), uuid4()
    previous_overrides = dict(app.dependency_overrides)
    app.dependency_overrides[get_db] = _db_override

    async with AsyncSessionLocal() as session:
        session.add_all(
            [
                Family(id=family_a, name="Write Alpha"),
                Family(id=family_b, name="Write Beta"),
                FamilyMember(
                    id=member_a,
                    family_id=family_a,
                    name="Ana",
                    relationship_type="PARENT",
                ),
                FamilyMember(
                    id=member_b,
                    family_id=family_b,
                    name="Ben",
                    relationship_type="PARENT",
                ),
            ]
        )
        await session.flush()
        await session.commit()

        try:
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                before_commitments = await session.scalar(
                    select(func.count(Commitment.id))
                )
                before_expenses = await session.scalar(
                    select(func.count(Expense.id))
                )

                commitment_response = await client.post(
                    "/api/v1/commitments",
                    json={
                        "family_id": str(family_a),
                        "member_id": str(member_b),
                        "commitment_type": "TASK",
                        "title": "Should not persist",
                    },
                )
                expense_response = await client.post(
                    "/api/v1/expenses",
                    json={
                        "family_id": str(family_a),
                        "member_id": str(member_b),
                        "amount": "45.00",
                        "category": "FOOD",
                        "expense_date": "2026-10-13",
                    },
                )
                invalid_family_write = await client.post(
                    "/api/v1/expenses",
                    json={
                        "family_id": str(uuid4()),
                        "member_id": str(member_a),
                        "amount": "45.00",
                        "category": "FOOD",
                        "expense_date": "2026-10-13",
                    },
                )

                unknown_member = uuid4()
                unknown_member_commitment = await client.post(
                    "/api/v1/commitments",
                    json={
                        "family_id": str(family_a),
                        "member_id": str(unknown_member),
                        "commitment_type": "TASK",
                        "title": "Unknown member task",
                    },
                )
                unknown_member_expense = await client.post(
                    "/api/v1/expenses",
                    json={
                        "family_id": str(family_a),
                        "member_id": str(unknown_member),
                        "amount": "45.00",
                        "category": "FOOD",
                        "expense_date": "2026-10-13",
                    },
                )

                # Foreign-member scope violations remain 400 Bad Request.
                assert commitment_response.status_code == 400
                assert expense_response.status_code == 400
                assert commitment_response.json()["code"] == "scope_violation"
                assert expense_response.json()["code"] == "scope_violation"

                # Missing families and members return 404 Not Found.
                assert invalid_family_write.status_code == 404
                assert unknown_member_commitment.status_code == 404
                assert unknown_member_expense.status_code == 404
                assert invalid_family_write.json()["code"] == "not_found"
                assert unknown_member_commitment.json()["code"] == "not_found"
                assert unknown_member_expense.json()["code"] == "not_found"

                assert (
                    await session.scalar(select(func.count(Commitment.id)))
                    == before_commitments
                )
                assert (
                    await session.scalar(select(func.count(Expense.id)))
                    == before_expenses
                )

        finally:
            await _cleanup(session, [family_a, family_b])
            app.dependency_overrides.clear()
            app.dependency_overrides.update(previous_overrides)


@pytest.mark.asyncio(loop_scope="session")
async def test_chat_api_does_not_leak_other_family_context_and_member_contract_is_undefined(
    monkeypatch,
):
    import app.services.chat as chat_module

    family_a, family_b = uuid4(), uuid4()
    member_a, member_b, unknown_member = uuid4(), uuid4(), uuid4()
    model = ScriptedAPIChatModel()
    monkeypatch.setattr(chat_module, "AIModelClient", lambda: model)
    previous_overrides = dict(app.dependency_overrides)
    app.dependency_overrides[get_db] = _db_override

    async with AsyncSessionLocal() as session:
        session.add_all(
            [
                Family(id=family_a, name="Chat Alpha"),
                Family(id=family_b, name="Chat Beta Secret"),
                FamilyMember(
                    id=member_a,
                    family_id=family_a,
                    name="Asha",
                    relationship_type="PARENT",
                ),
                FamilyMember(
                    id=member_b,
                    family_id=family_b,
                    name="B Secret",
                    relationship_type="PARENT",
                ),
                _commitment(
                    family_a,
                    member_a,
                    "Alpha obligation",
                    date(2026, 10, 20),
                ),
                _commitment(
                    family_b,
                    member_b,
                    "Beta confidential obligation",
                    date(2026, 10, 20),
                ),
            ]
        )
        await session.flush()
        await session.commit()

        try:
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                valid = await client.post(
                    "/api/v1/chat",
                    json={
                        "family_id": str(family_a),
                        "member_id": str(member_a),
                        "message": "Hello",
                    },
                )
                foreign_member = await client.post(
                    "/api/v1/chat",
                    json={
                        "family_id": str(family_a),
                        "member_id": str(member_b),
                        "message": "Hello",
                    },
                )
                unknown_member_response = await client.post(
                    "/api/v1/chat",
                    json={
                        "family_id": str(family_a),
                        "member_id": str(unknown_member),
                        "message": "Hello",
                    },
                )

                assert (
                    valid.status_code
                    == foreign_member.status_code
                    == unknown_member_response.status_code
                    == 200
                )

                system_prompt = model.calls[0][0]["content"]
                assert "Asha" in system_prompt
                assert "Alpha obligation" in system_prompt
                assert "Chat Beta Secret" not in system_prompt
                assert "B Secret" not in system_prompt
                assert "Beta confidential obligation" not in system_prompt
                assert "The person speaking is Asha" in system_prompt

                # Unknown/foreign chat member IDs do not add member context.
                assert "The person speaking is" not in model.calls[1][0]["content"]
                assert "The person speaking is" not in model.calls[2][0]["content"]

        finally:
            await _cleanup(session, [family_a, family_b])
            app.dependency_overrides.clear()
            app.dependency_overrides.update(previous_overrides)
