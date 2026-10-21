"""Agent-to-tool-to-PostgreSQL integration coverage using a scripted model."""

from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import delete, select

from app.agents.orchestrator import FamilyContextAgent
from app.agents.state import AgentState
from app.clients.ai_model import AIResponse, ToolCallRequest
from app.db.session import AsyncSessionLocal
from app.models.expense import Expense
from app.models.family import Family
from app.models.family_member import FamilyMember
from app.repositories.commitment import CommitmentRepository
from app.repositories.expense import ExpenseRepository
from app.repositories.notification import NotificationRepository
from app.services.commitment import CommitmentService
from app.services.expense import ExpenseService
from app.services.notification import NotificationService
from app.services.priority import PriorityService
from app.tools.registry import ToolRegistry


class ScriptedExpenseAI:
    """Select add_expense once, then return a fixed response after its result."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def chat(self, *, messages, tools=None, **_kwargs):
        self.calls.append({"messages": messages, "tools": tools})
        if len(self.calls) == 1:
            return AIResponse(
                content=None,
                tool_calls=[
                    ToolCallRequest(
                        name="add_expense",
                        arguments={"amount": "1850", "category": "groceries"},
                        call_id="expense-call",
                    )
                ],
            )
        return AIResponse(content="Recorded the grocery expense.", tool_calls=[])


@pytest.mark.asyncio(loop_scope="session")
async def test_agent_add_expense_persists_exactly_one_row_in_postgres(monkeypatch) -> None:
    from app.agents import orchestrator
    from app.utils import dates

    family_id = uuid4()
    member_id = uuid4()
    today = date(2026, 10, 13)
    monkeypatch.setattr(dates, "today_in", lambda _timezone: today)
    monkeypatch.setattr(
        orchestrator,
        "get_settings",
        lambda: SimpleNamespace(family_timezone="Asia/Kolkata"),
    )

    async with AsyncSessionLocal() as session:
        family = Family(id=family_id, name="Agent Expense Integration Family")
        member = FamilyMember(
            id=member_id,
            family_id=family_id,
            name="Test Member",
            relationship_type="PARENT",
        )
        session.add_all([family, member])
        await session.flush()

        expense_repository = ExpenseRepository(session)
        commitment_repository = CommitmentRepository(session)
        priority_service = PriorityService(
            commitment_repository,
            NotificationService(NotificationRepository(session)),
        )
        registry = ToolRegistry(
            expense_service=ExpenseService(expense_repository),
            commitment_service=CommitmentService(commitment_repository),
            priority_service=priority_service,
        )
        model = ScriptedExpenseAI()
        agent = FamilyContextAgent(model, registry)  # type: ignore[arg-type]

        try:
            result = await agent.run(
                AgentState(
                    family_id=family_id,
                    member_id=member_id,
                    conversation_id=None,
                    user_message="I spent ₹1850 on groceries today.",
                )
            )

            assert result.tool_calls[0]["name"] == "add_expense"
            assert len(result.tool_calls) == 1
            assert "add_expense" in {
                item["function"]["name"] for item in model.calls[0]["tools"]
            }
            assert len(model.calls) == 2
            assert model.calls[1]["messages"][-1]["role"] == "tool"
            tool_result = result.tool_results[0]["result"]
            assert tool_result["success"] is True
            assert tool_result["amount"] == "1850.00"
            assert tool_result["category"] == "GROCERIES"
            assert tool_result["expense_date"] == today.isoformat()
            assert result.assistant_message == "Recorded the grocery expense."

            expenses = list(
                (
                    await session.scalars(
                        select(Expense).where(Expense.family_id == family_id)
                    )
                ).all()
            )
            assert len(expenses) == 1
            expense = expenses[0]
            assert str(expense.id) == tool_result["expense_id"]
            assert expense.family_id == family_id
            assert expense.member_id == member_id
            assert expense.amount == Decimal("1850.00")
            assert expense.category == "GROCERIES"
            assert expense.expense_date == today
        finally:
            await session.rollback()
            await session.execute(delete(Family).where(Family.id == family_id))
            await session.commit()
