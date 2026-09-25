from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.commitment import Commitment
from app.models.commitment_dependency import CommitmentDependency
from app.models.expense import Expense
from app.models.family import Family
from app.repositories.commitment import CommitmentRepository
from app.repositories.expense import ExpenseRepository
from app.services.commitment import CommitmentService
from app.services.expense import ExpenseService
from app.tools.registry import ToolRegistry


@pytest.mark.asyncio(loop_scope="session")
async def test_all_seven_tools_with_postgres():
    """
    End-to-end integration test for all seven Team 2 tools.

    Flow:

        ToolRegistry
            ↓
        Agent Tools
            ↓
        Services
            ↓
        Repositories
            ↓
        PostgreSQL
    """

    async with AsyncSessionLocal() as session:

        # ============================================================
        # 1. CREATE TEST FAMILY
        # ============================================================

        family = Family(
            id=uuid4(),
            name="All Tools Integration Test Family",
        )

        session.add(family)
        await session.flush()

        family_id = family.id

        # ============================================================
        # 2. CREATE REAL SERVICES
        # ============================================================

        expense_repository = ExpenseRepository(session)
        expense_service = ExpenseService(expense_repository)

        commitment_repository = CommitmentRepository(session)
        commitment_service = CommitmentService(commitment_repository)

        # ============================================================
        # 3. CREATE REAL TOOL REGISTRY
        # ============================================================

        registry = ToolRegistry(
            expense_service=expense_service,
            commitment_service=commitment_service,
        )

        # ============================================================
        # TOOL 1
        # add_expense
        # ============================================================

        expense_result = await registry.dispatch(
            "add_expense",
            {
                "family_id": str(family_id),
                "amount": "850.00",
                "category": "groceries",
                "merchant": "Supermarket",
                "description": "Weekly groceries",
                "expense_date": str(date.today()),
                "source": "TEXT",
            },
        )

        print("\n1. ADD EXPENSE")
        print(expense_result)

        assert expense_result["success"] is True
        assert expense_result["message"] == "Expense recorded"
        assert "expense_id" in expense_result

        expense_id = UUID(expense_result["expense_id"])

        saved_expense = await session.scalar(
            select(Expense).where(
                Expense.id == expense_id,
                Expense.family_id == family_id,
            )
        )

        assert saved_expense is not None
        assert saved_expense.amount == Decimal("850.00")
        assert saved_expense.category == "GROCERIES"
        assert saved_expense.merchant == "Supermarket"
        assert saved_expense.description == "Weekly groceries"
        assert saved_expense.expense_date == date.today()
        assert saved_expense.source == "TEXT"

        # ============================================================
        # TOOL 2
        # get_expense_summary
        # ============================================================

        second_expense = await registry.dispatch(
            "add_expense",
            {
                "family_id": str(family_id),
                "amount": "500.00",
                "category": "groceries",
                "merchant": "Local Store",
                "description": "Vegetables",
                "expense_date": str(date.today()),
                "source": "TEXT",
            },
        )

        assert second_expense["success"] is True

        summary_result = await registry.dispatch(
            "get_expense_summary",
            {
                "family_id": str(family_id),
                "category": "groceries",
            },
        )

        print("\n2. GET EXPENSE SUMMARY")
        print(summary_result)

        assert summary_result["total"] == "1350.00"
        assert summary_result["transaction_count"] == 2

        # ============================================================
        # TOOL 3
        # create_commitment
        # ============================================================

        commitment_result = await registry.dispatch(
            "create_commitment",
            {
                "family_id": str(family_id),
                "commitment_type": "BILL",
                "category": "utilities",
                "title": "Electricity Bill",
                "description": "Pay monthly electricity bill",
                "amount": "2500.00",
                "start_date": str(date.today()),
                "due_date": str(date.today() + timedelta(days=7)),
                "status": "PENDING",
                "priority": "HIGH",
                "source_type": "TEXT",
            },
        )

        print("\n3. CREATE COMMITMENT")
        print(commitment_result)

        assert commitment_result["success"] is True
        assert "commitment_id" in commitment_result
        assert commitment_result["status"] == "PENDING"

        commitment_id = UUID(commitment_result["commitment_id"])

        saved_commitment = await session.scalar(
            select(Commitment).where(
                Commitment.id == commitment_id,
                Commitment.family_id == family_id,
            )
        )

        assert saved_commitment is not None
        assert saved_commitment.title == "Electricity Bill"
        assert saved_commitment.category == "UTILITIES"
        assert saved_commitment.amount == Decimal("2500.00")
        assert saved_commitment.status == "PENDING"
        assert saved_commitment.priority == "HIGH"

        # ============================================================
        # CREATE SECOND COMMITMENT
        #
        # This is used by search, dependency and priority tests.
        # ============================================================

        second_commitment_result = await registry.dispatch(
            "create_commitment",
            {
                "family_id": str(family_id),
                "commitment_type": "TASK",
                "category": "shopping",
                "title": "Buy School Supplies",
                "description": "Purchase notebooks and stationery",
                "start_date": str(date.today()),
                "due_date": str(date.today() + timedelta(days=3)),
                "status": "PENDING",
                "priority": "MEDIUM",
                "source_type": "TEXT",
            },
        )

        assert second_commitment_result["success"] is True

        second_commitment_id = UUID(
            second_commitment_result["commitment_id"]
        )

        # ============================================================
        # TOOL 4
        # search_commitments
        # ============================================================

        search_result = await registry.dispatch(
            "search_commitments",
            {
                "family_id": str(family_id),
                "category": "utilities",
            },
        )

        print("\n4. SEARCH COMMITMENTS")
        print(search_result)

        assert search_result["success"] is True
        assert "commitments" in search_result
        assert len(search_result["commitments"]) >= 1

        matching_commitment = next(
            (
                item
                for item in search_result["commitments"]
                if str(item["id"]) == str(commitment_id)
            ),
            None,
        )

        assert matching_commitment is not None
        assert matching_commitment["title"] == "Electricity Bill"

        # ============================================================
        # TOOL 5
        # update_commitment
        # ============================================================

        update_result = await registry.dispatch(
            "update_commitment",
            {
                "commitment_id": str(commitment_id),
                "family_id": str(family_id),
                "status": "IN_PROGRESS",
                "priority": "HIGH",
                "due_date": str(date.today() + timedelta(days=10)),
            },
        )

        print("\n5. UPDATE COMMITMENT")
        print(update_result)

        assert update_result["success"] is True
        assert update_result["commitment_id"] == str(commitment_id)
        assert update_result["status"] == "IN_PROGRESS"

        updated_commitment = await session.scalar(
            select(Commitment).where(
                Commitment.id == commitment_id,
                Commitment.family_id == family_id,
            )
        )

        assert updated_commitment is not None
        assert updated_commitment.status == "IN_PROGRESS"
        assert updated_commitment.priority == "HIGH"
        assert updated_commitment.due_date == date.today() + timedelta(days=10)

        # ============================================================
        # TOOL 6
        # create_dependency
        # ============================================================

        dependency_result = await registry.dispatch(
            "create_dependency",
            {
                "family_id": str(family_id),
                "source_commitment_id": str(commitment_id),
                "target_commitment_id": str(second_commitment_id),
                "relationship_type": "MUST_COMPLETE_BEFORE",
            },
        )

        print("\n6. CREATE DEPENDENCY")
        print(dependency_result)

        assert dependency_result["success"] is True
        assert dependency_result["message"] == "Dependency created"

        dependency = await session.scalar(
            select(CommitmentDependency).where(
                CommitmentDependency.family_id == family_id,
                CommitmentDependency.source_commitment_id == commitment_id,
                CommitmentDependency.target_commitment_id
                == second_commitment_id,
            )
        )

        assert dependency is not None
        assert dependency.dependency_type == "MUST_COMPLETE_BEFORE"

        # ============================================================
        # TOOL 7
        # get_family_priorities
        # ============================================================

        priority_result = await registry.dispatch(
            "get_family_priorities",
            {
                "family_id": str(family_id),
            },
        )

        print("\n7. GET FAMILY PRIORITIES")
        print(priority_result)

        assert priority_result["success"] is True
        assert "commitments" in priority_result

        priority_commitment = next(
            (
                item
                for item in priority_result["commitments"]
                if str(item["id"]) == str(commitment_id)
            ),
            None,
        )

        assert priority_commitment is not None
        assert priority_commitment["title"] == "Electricity Bill"
        assert priority_commitment["priority"] == "HIGH"

        # ============================================================
        # FINAL VERIFICATION
        # ============================================================

        print("\n" + "=" * 60)
        print("ALL 7 TEAM 2 TOOLS PASSED")
        print("=" * 60)

        # Roll back everything created by this integration test.
        await session.rollback()