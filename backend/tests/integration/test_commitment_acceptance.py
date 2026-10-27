from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.agents.orchestrator import FamilyContextAgent
from app.agents.state import AgentState
from app.clients.ai_model import AIResponse, ToolCallRequest
from app.db.session import AsyncSessionLocal
from app.models.commitment import Commitment
from app.models.family import Family
from app.repositories.commitment import CommitmentRepository
from app.repositories.expense import ExpenseRepository
from app.services.commitment import CommitmentService
from app.services.expense import ExpenseService
from app.tools.registry import ToolRegistry


class FakeAIClient:
    """Return a deterministic commitment tool call."""

    def __init__(self):
        self.call_count = 0

    async def chat(self, *, messages, tools=None, **kwargs):
        self.call_count += 1

        if self.call_count == 1:
            return AIResponse(
                content=None,
                tool_calls=[
                    ToolCallRequest(
                        name="create_commitment",
                        arguments={
                            "commitment_type": "BILL",
                            "title": "Electricity bill",
                            "amount": "3240.00",
                            "category": "utilities",
                            "description": "Electricity bill due October 25",
                            "status": "PENDING",
                            "priority": "HIGH",
                            "source_type": "TEXT",
                        },
                        call_id="electricity-bill-call",
                    )
                ],
            )

        return AIResponse(
            content="Electricity bill recorded.",
            tool_calls=[],
        )


class EmptyPriorityService:
    async def attention_items(self, family_id):
        return []


@pytest.mark.asyncio(loop_scope="session")
async def test_electricity_bill_is_resolved_and_saved_in_postgres(
    monkeypatch,
):
    """Verify agent date resolution and real PostgreSQL persistence."""
    async with AsyncSessionLocal() as session:
        family = Family(
            id=uuid4(),
            name="Electricity Bill Acceptance Test Family",
        )
        session.add(family)
        await session.flush()

        family_id = family.id

        expense_service = ExpenseService(ExpenseRepository(session))
        commitment_service = CommitmentService(
            CommitmentRepository(session)
        )

        registry = ToolRegistry(
            expense_service=expense_service,
            commitment_service=commitment_service,
            priority_service=EmptyPriorityService(),  # type: ignore[arg-type]
        )

        agent = FamilyContextAgent(
            FakeAIClient(),  # type: ignore[arg-type]
            registry,
        )

        state = AgentState(
            family_id=family_id,
            member_id=None,
            conversation_id=None,
            user_message="Electricity bill ₹3,240 due October 25",
            metadata={"today": "2026-10-24"},
        )

        monkeypatch.setattr(
            "app.tools.commitment_tools._today",
            lambda: date(2026, 10, 24),
        )

        result = await agent.run(state)

        assert result.tool_results, (
            f"Agent did not execute a tool. Message: "
            f"{result.assistant_message}"
        )
        assert result.tool_results[0]["tool"] == "create_commitment"

        tool_result = result.tool_results[0]["result"]
        assert tool_result["success"] is True, tool_result

        commitment_id = tool_result.get("commitment_id") or tool_result.get(
            "id"
        )
        assert commitment_id is not None, tool_result

        saved_commitment = await session.scalar(
            select(Commitment).where(
                Commitment.id == commitment_id,
                Commitment.family_id == family_id,
            )
        )

        assert saved_commitment is not None
        assert saved_commitment.title == "Electricity bill"
        assert saved_commitment.commitment_type == "BILL"
        assert saved_commitment.amount == Decimal("3240.00")
        assert saved_commitment.due_date == date(2026, 10, 25)
