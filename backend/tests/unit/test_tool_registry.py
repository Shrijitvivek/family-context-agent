"""Focused tests for all registered tools in the ToolRegistry."""

from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

import pytest
from app.core.constants import CommitmentStatus
from app.core.exceptions import DuplicateCommitmentError, ToolInputValidationError
from app.models.commitment import Commitment
from app.schemas.expense import ExpenseSummary
from app.services.commitment import CommitmentService
from app.services.expense import ExpenseService
from app.tools.registry import ToolRegistry


class FakeExpenseRepository:
    def __init__(self) -> None:
        self.added: list[Any] = []
        self.commits = 0
        self.scope_checks: list[Any] = []

    async def assert_scope(self, family_id: UUID, member_id: UUID | None = None) -> None:
        self.scope_checks.append((family_id, member_id))

    async def add(self, expense):
        expense.id = uuid4()
        self.added.append(expense)
        return expense

    async def summary(self, query) -> ExpenseSummary:
        return ExpenseSummary(
            total=Decimal("3050.00"),
            transaction_count=2,
            category=query.category,
            start_date=query.start_date,
            end_date=query.end_date,
        )

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        raise AssertionError("rollback should not be called")


class FakeCommitmentRepository:
    def __init__(self, candidates: list[Commitment] | None = None) -> None:
        self.candidates = candidates or []
        self.added: list[Commitment] = []
        self.commits = 0
        self.scope_checks: list[Any] = []

    async def assert_scope(self, family_id: UUID, *, member_id=None, document_id=None) -> None:
        self.scope_checks.append((family_id, member_id, document_id))

    async def find_likely_duplicates(self, **kwargs) -> list[Commitment]:
        return self.candidates

    async def search(self, query) -> list[Commitment]:
        self.scope_checks.append((query.family_id, query.member_id, None))
        return self.candidates

    async def update(self, payload) -> Commitment:
        self.scope_checks.append((payload.family_id, None, None))
        commitment = self.added[0] if self.added else self.candidates[0]
        if payload.status:
            commitment.status = payload.status.value
        return commitment

    async def add_dependency(self, payload):
        self.scope_checks.append((payload.family_id, None, None))
        return type("CommitmentDependency", (), {"id": uuid4()})()

    async def get_priorities(self, query) -> list[Commitment]:
        self.scope_checks.append((query.family_id, None, None))
        return self.candidates

    async def add(self, commitment: Commitment) -> Commitment:
        commitment.id = uuid4()
        self.added.append(commitment)
        return commitment

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        raise AssertionError("rollback should not be called")


@pytest.mark.asyncio
async def test_registry_executes_the_first_three_tools() -> None:
    family_id = uuid4()
    expense_repository = FakeExpenseRepository()
    commitment_repository = FakeCommitmentRepository()
    registry = ToolRegistry(
        ExpenseService(expense_repository),  # type: ignore[arg-type]
        CommitmentService(commitment_repository),  # type: ignore[arg-type]
    )

    expense_result = await registry.dispatch(
        "add_expense",
        {
            "family_id": str(family_id),
            "amount": "1850.00",
            "category": "groceries",
            "merchant": "Lulu Hypermarket",
            "expense_date": "2026-10-05",
        },
    )
    assert expense_result["success"] is True
    assert expense_repository.added[0].category == "GROCERIES"
    assert expense_repository.commits == 1

    summary_result = await registry.dispatch(
        "get_expense_summary",
        {
            "family_id": str(family_id),
            "category": "groceries",
            "start_date": "2026-10-01",
            "end_date": "2026-10-31",
        },
    )
    assert summary_result["total"] == "3050.00"
    assert summary_result["transaction_count"] == 2

    commitment_result = await registry.dispatch(
        "create_commitment",
        {
            "family_id": str(family_id),
            "commitment_type": "BILL",
            "category": "electricity",
            "title": "Electricity Bill",
            "amount": "3240.00",
            "due_date": "2026-10-18",
            "source_type": "TEXT",
        },
    )
    assert commitment_result["success"] is True
    assert commitment_result["status"] == CommitmentStatus.PENDING.value
    assert commitment_repository.added[0].category == "ELECTRICITY"
    assert commitment_repository.commits == 1

    search_result = await registry.dispatch(
        "search_commitments",
        {
            "family_id": str(family_id),
            "status": "PENDING",
            "category": "electricity",
        },
    )
    assert search_result["success"] is True
    assert isinstance(search_result["commitments"], list)

    update_result = await registry.dispatch(
        "update_commitment",
        {
            "commitment_id": str(commitment_repository.added[0].id),
            "family_id": str(family_id),
            "status": "COMPLETED",
        }
    )
    assert update_result["success"] is True
    assert update_result["status"] == "COMPLETED"

    dependency_result = await registry.dispatch(
        "create_dependency",
        {
            "family_id": str(family_id),
            "source_commitment_id": str(uuid4()),
            "target_commitment_id": str(uuid4()),
            "relationship_type": "MUST_COMPLETE_BEFORE",
        }
    )
    assert dependency_result["success"] is True

    priorities_result = await registry.dispatch(
        "get_family_priorities",
        {
            "family_id": str(family_id),
        }
    )
    assert priorities_result["success"] is True

    assert registry.names == (
        "add_expense",
        "get_expense_summary",
        "create_commitment",
        "search_commitments",
        "update_commitment",
        "create_dependency",
        "get_family_priorities",
    )


@pytest.mark.asyncio
async def test_create_commitment_returns_duplicate_candidates_for_clarification() -> None:
    family_id = uuid4()
    existing = Commitment(
        id=uuid4(),
        family_id=family_id,
        commitment_type="BILL",
        category="ELECTRICITY",
        title="Electricity Bill",
        amount=Decimal("3240.00"),
        due_date=date(2026, 10, 18),
        status="PENDING",
        priority="MEDIUM",
        source_type="TEXT",
    )
    registry = ToolRegistry(
        ExpenseService(FakeExpenseRepository()),  # type: ignore[arg-type]
        CommitmentService(FakeCommitmentRepository([existing])),  # type: ignore[arg-type]
    )

    with pytest.raises(DuplicateCommitmentError) as error:
        await registry.dispatch(
            "create_commitment",
            {
                "family_id": str(family_id),
                "commitment_type": "BILL",
                "category": "electricity",
                "title": "Electricity Bill",
                "due_date": "2026-10-18",
            },
        )

    assert error.value.details["candidates"][0]["commitment_id"] == str(existing.id)


@pytest.mark.asyncio
async def test_registry_rejects_incomplete_or_unknown_tool_calls() -> None:
    registry = ToolRegistry(
        ExpenseService(FakeExpenseRepository()),  # type: ignore[arg-type]
        CommitmentService(FakeCommitmentRepository()),  # type: ignore[arg-type]
    )

    with pytest.raises(ToolInputValidationError):
        await registry.dispatch("add_expense", {"category": "GROCERIES"})
    with pytest.raises(ToolInputValidationError):
        await registry.dispatch("drop_database", {})
