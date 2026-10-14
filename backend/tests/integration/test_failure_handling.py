"""Failure-path checks for API transactions, agent tools, and background work."""

from datetime import date
from decimal import Decimal
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.exc import SQLAlchemyError

from app.agents.state import AgentState
from app.api.dependencies import get_db
from app.clients.ai_model import AIResponse, ToolCallRequest
from app.core.constants import CommitmentStatus, CommitmentType, Priority, SourceType
from app.core.exceptions import AIModelError
from app.db.session import AsyncSessionLocal
from app.jobs import deadline_checks
from app.main import app
from app.models.commitment import Commitment
from app.models.expense import Expense
from app.models.family import Family
from app.models.family_member import FamilyMember
from app.models.notification import Notification
from app.repositories.commitment import CommitmentRepository
from app.repositories.expense import ExpenseRepository
from app.repositories.family import FamilyRepository
from app.services.priority import NotificationService, PriorityService


class ScriptedActionThenClaimModel:
    def __init__(self):
        self.calls = 0

    async def chat(self, *, messages, tools=None, **_kwargs):
        self.calls += 1
        if self.calls == 1:
            return AIResponse(content="Ready to help.", tool_calls=[])
        if self.calls == 2:
            return AIResponse(content=None, tool_calls=[ToolCallRequest(
                name="add_expense",
                arguments={"amount": "45.00", "category": "FOOD"},
                call_id="fail-expense",
            )])
        # Deliberately claim success after the real tool reports persistence failure.
        return AIResponse(content="The ₹45 food expense was recorded successfully.", tool_calls=[])


class UnavailableModel:
    async def chat(self, **_kwargs):
        raise AIModelError("scripted model unavailable")


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


async def _count(model, family_id):
    async with AsyncSessionLocal() as session:
        return await session.scalar(select(func.count(model.id)).where(model.family_id == family_id))


def _commitment_payload(family_id, member_id, title="Failure Test Task"):
    return {
        "family_id": str(family_id), "member_id": str(member_id),
        "commitment_type": "TASK", "category": "HOME", "title": title,
        "description": "original description", "amount": "100.00",
        "due_date": "2026-10-20", "status": "PENDING", "priority": "MEDIUM",
        "source_type": "MANUAL",
    }


@pytest.mark.asyncio(loop_scope="session")
async def test_api_persistence_failures_rollback_expense_commitment_create_and_update_then_retry(monkeypatch):
    family_id, member_id = uuid4(), uuid4()
    previous_overrides = dict(app.dependency_overrides)
    app.dependency_overrides[get_db] = _db_override
    async with AsyncSessionLocal() as session:
        session.add_all([
            Family(id=family_id, name="Failure Atomicity Family"),
            FamilyMember(id=member_id, family_id=family_id, name="Test", relationship_type="PARENT"),
        ])
        await session.commit()
        try:
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                original_expense_commit = ExpenseRepository.commit
                expense_failures = {"remaining": 1}

                async def fail_expense_commit_once(repository):
                    if expense_failures["remaining"]:
                        expense_failures["remaining"] -= 1
                        raise SQLAlchemyError("controlled internal database detail")
                    await original_expense_commit(repository)

                monkeypatch.setattr(ExpenseRepository, "commit", fail_expense_commit_once)
                expense_payload = {
                    "family_id": str(family_id), "member_id": str(member_id),
                    "amount": "45.00", "category": "FOOD", "expense_date": "2026-10-13",
                }
                failed_expense = await client.post("/api/v1/expenses", json=expense_payload)
                assert failed_expense.status_code == 400
                assert failed_expense.json()["code"] == "persistence_error"
                assert "controlled internal database detail" not in failed_expense.text
                assert await _count(Expense, family_id) == 0
                retried_expense = await client.post("/api/v1/expenses", json=expense_payload)
                assert retried_expense.status_code == 201
                assert await _count(Expense, family_id) == 1

                original_commitment_commit = CommitmentRepository.commit
                commitment_failures = {"remaining": 1}

                async def fail_commitment_create_once(repository):
                    if commitment_failures["remaining"]:
                        commitment_failures["remaining"] -= 1
                        raise SQLAlchemyError("controlled commitment commit detail")
                    await original_commitment_commit(repository)

                monkeypatch.setattr(CommitmentRepository, "commit", fail_commitment_create_once)
                failed_create = await client.post("/api/v1/commitments", json=_commitment_payload(family_id, member_id))
                assert failed_create.status_code == 400
                assert failed_create.json()["code"] == "persistence_error"
                assert "controlled commitment commit detail" not in failed_create.text
                assert await _count(Commitment, family_id) == 0

                created = await client.post("/api/v1/commitments", json=_commitment_payload(family_id, member_id))
                assert created.status_code == 201
                commitment_id = created.json()["id"]
                assert await _count(Commitment, family_id) == 1

                update_failures = {"remaining": 1}

                async def fail_update_commit_once(repository):
                    if update_failures["remaining"]:
                        update_failures["remaining"] -= 1
                        raise SQLAlchemyError("controlled update commit detail")
                    await original_commitment_commit(repository)

                monkeypatch.setattr(CommitmentRepository, "commit", fail_update_commit_once)
                failed_update = await client.patch(
                    f"/api/v1/commitments/{commitment_id}",
                    json={"family_id": str(family_id), "status": "COMPLETED", "amount": "250.00", "due_date": "2026-10-28"},
                )
                assert failed_update.status_code == 400
                assert failed_update.json()["code"] == "persistence_error"
                assert "controlled update commit detail" not in failed_update.text
                async with AsyncSessionLocal() as verify:
                    unchanged = await verify.get(Commitment, commitment_id)
                    assert unchanged.status == CommitmentStatus.PENDING.value
                    assert unchanged.amount == Decimal("100.00")
                    assert unchanged.due_date == date(2026, 10, 20)
                    assert await verify.scalar(select(func.count(Commitment.id)).where(Commitment.family_id == family_id)) == 1

                retried_update = await client.patch(
                    f"/api/v1/commitments/{commitment_id}",
                    json={"family_id": str(family_id), "status": "COMPLETED", "amount": "250.00", "due_date": "2026-10-28"},
                )
                assert retried_update.status_code == 200
                assert retried_update.json()["status"] == "COMPLETED"
                async with AsyncSessionLocal() as verify:
                    updated = await verify.get(Commitment, commitment_id)
                    assert updated.amount == Decimal("250.00")
                    assert updated.due_date == date(2026, 10, 28)
                    assert await verify.scalar(select(func.count(Commitment.id)).where(Commitment.family_id == family_id)) == 1
        finally:
            await _cleanup(session, [family_id])
            app.dependency_overrides.clear()
            app.dependency_overrides.update(previous_overrides)


@pytest.mark.asyncio(loop_scope="session")
async def test_chat_does_not_claim_success_after_expense_persistence_failure(monkeypatch):
    import app.services.chat as chat_module

    family_id, member_id = uuid4(), uuid4()
    model = ScriptedActionThenClaimModel()
    monkeypatch.setattr(chat_module, "AIModelClient", lambda: model)
    original_commit = ExpenseRepository.commit

    async def fail_expense_commit(_repository):
        raise SQLAlchemyError("controlled expense commit failure")

    monkeypatch.setattr(ExpenseRepository, "commit", fail_expense_commit)
    previous_overrides = dict(app.dependency_overrides)
    app.dependency_overrides[get_db] = _db_override
    async with AsyncSessionLocal() as session:
        session.add_all([
            Family(id=family_id, name="Agent Failure Family"),
            FamilyMember(id=member_id, family_id=family_id, name="Member", relationship_type="PARENT"),
        ])
        await session.commit()
        try:
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                first_turn = await client.post("/api/v1/chat", json={
                    "family_id": str(family_id), "member_id": str(member_id), "message": "Hello",
                })
                assert first_turn.status_code == 200
                response = await client.post("/api/v1/chat", json={
                    "family_id": str(family_id), "member_id": str(member_id),
                    "conversation_id": first_turn.json()["conversation_id"],
                    "message": "I spent ₹45 on food today.",
                })
            assert response.status_code == 200
            payload = response.json()
            assert "not completed successfully" in payload["message"]
            assert "recorded successfully" not in payload["message"]
            assert "saved" in payload["message"]
            assert payload["tool_results"][0]["result"]["success"] is False
            assert await _count(Expense, family_id) == 0
        finally:
            monkeypatch.setattr(ExpenseRepository, "commit", original_commit)
            await _cleanup(session, [family_id])
            app.dependency_overrides.clear()
            app.dependency_overrides.update(previous_overrides)


@pytest.mark.asyncio(loop_scope="session")
async def test_chat_preserves_normal_successful_expense_response(monkeypatch):
    import app.services.chat as chat_module

    family_id, member_id = uuid4(), uuid4()
    model = ScriptedActionThenClaimModel()
    monkeypatch.setattr(chat_module, "AIModelClient", lambda: model)
    previous_overrides = dict(app.dependency_overrides)
    app.dependency_overrides[get_db] = _db_override
    async with AsyncSessionLocal() as session:
        session.add_all([
            Family(id=family_id, name="Successful Agent Action Family"),
            FamilyMember(id=member_id, family_id=family_id, name="Member", relationship_type="PARENT"),
        ])
        await session.commit()
        try:
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                first_turn = await client.post("/api/v1/chat", json={
                    "family_id": str(family_id), "member_id": str(member_id), "message": "Hello",
                })
                assert first_turn.status_code == 200
                response = await client.post("/api/v1/chat", json={
                    "family_id": str(family_id), "member_id": str(member_id),
                    "conversation_id": first_turn.json()["conversation_id"],
                    "message": "I spent â‚¹45 on food today.",
                })
            assert response.status_code == 200
            payload = response.json()
            assert "recorded successfully" in payload["message"]
            assert payload["tool_results"][0]["result"]["success"] is True
            assert await _count(Expense, family_id) == 1
        finally:
            await _cleanup(session, [family_id])
            app.dependency_overrides.clear()
            app.dependency_overrides.update(previous_overrides)


@pytest.mark.asyncio(loop_scope="session")
async def test_model_unavailable_returns_error_without_persisting_chat_action(monkeypatch):
    import app.services.chat as chat_module

    family_id, member_id = uuid4(), uuid4()
    monkeypatch.setattr(chat_module, "AIModelClient", UnavailableModel)
    previous_overrides = dict(app.dependency_overrides)
    app.dependency_overrides[get_db] = _db_override
    async with AsyncSessionLocal() as session:
        session.add_all([
            Family(id=family_id, name="Unavailable Model Family"),
            FamilyMember(id=member_id, family_id=family_id, name="Member", relationship_type="PARENT"),
        ])
        await session.commit()
        try:
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post("/api/v1/chat", json={
                    "family_id": str(family_id), "member_id": str(member_id),
                    "message": "Record my expense.",
                })
            assert response.status_code == 400
            assert response.json()["code"] == "ai_model_unavailable"
            assert "success" not in response.text.casefold()
            assert await _count(Expense, family_id) == 0
            assert await _count(Commitment, family_id) == 0
        finally:
            await _cleanup(session, [family_id])
            app.dependency_overrides.clear()
            app.dependency_overrides.update(previous_overrides)


@pytest.mark.asyncio(loop_scope="session")
async def test_background_database_failure_rolls_back_failed_family_and_processes_other(monkeypatch, caplog):
    failed_family, healthy_family = uuid4(), uuid4()
    today = date(2026, 10, 13)
    async with AsyncSessionLocal() as session:
        session.add_all([
            Family(id=failed_family, name="Background DB Failure Family"),
            Family(id=healthy_family, name="Background DB Healthy Family"),
            Commitment(
                id=uuid4(), family_id=failed_family, commitment_type="TASK", category="HOME",
                title="Will remain pending", due_date=date(2026, 10, 12), status="PENDING",
                priority="MEDIUM", source_type="MANUAL",
            ),
            Commitment(
                id=uuid4(), family_id=healthy_family, commitment_type="TASK", category="HOME",
                title="Will become overdue", due_date=date(2026, 10, 12), status="PENDING",
                priority="MEDIUM", source_type="MANUAL",
            ),
        ])
        await session.commit()
        original_list = FamilyRepository.list_families
        original_sync = NotificationService.sync
        monkeypatch.setattr(deadline_checks, "today_in", lambda _timezone: today)

        async def list_only_test_families(repository):
            return [f for f in await original_list(repository) if f.id in {failed_family, healthy_family}]

        async def fail_notification_sync_once(service, family_id, assessments):
            if family_id == failed_family:
                raise SQLAlchemyError("controlled notification persistence failure")
            return await original_sync(service, family_id, assessments)

        monkeypatch.setattr(FamilyRepository, "list_families", list_only_test_families)
        monkeypatch.setattr(NotificationService, "sync", fail_notification_sync_once)
        try:
            processed_families = await deadline_checks.run_deadline_checks()
            assert processed_families == 2
            assert "priority_refresh_failed" in caplog.text
            async with AsyncSessionLocal() as verify:
                failed = list((await verify.scalars(select(Commitment).where(Commitment.family_id == failed_family))).all())
                healthy = list((await verify.scalars(select(Commitment).where(Commitment.family_id == healthy_family))).all())
                assert len(failed) == len(healthy) == 1
                assert failed[0].status == CommitmentStatus.PENDING.value
                assert healthy[0].status == CommitmentStatus.OVERDUE.value
                assert await verify.scalar(select(func.count(Notification.id)).where(Notification.family_id == failed_family)) == 0
                assert await verify.scalar(select(func.count(Notification.id)).where(Notification.family_id == healthy_family)) == 1
        finally:
            await _cleanup(session, [failed_family, healthy_family])
