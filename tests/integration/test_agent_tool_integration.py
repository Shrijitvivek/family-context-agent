from datetime import date
from typing import cast
from uuid import uuid4

import pytest
from sqlalchemy import delete, select

from app.agents.orchestrator import FamilyContextAgent
from app.agents.state import AgentState
from app.clients.ai_model import AIModelClient, AIResponse, ToolCallRequest
from app.db.session import AsyncSessionLocal
from app.models.expense import Expense
from app.models.family import Family
from app.repositories.commitment import CommitmentRepository
from app.repositories.expense import ExpenseRepository
from app.services.commitment import CommitmentService
from app.services.expense import ExpenseService
from app.tools.registry import ToolRegistry


class MockAIClient:
    """
    Fake AI client used for integration testing.

    First call:
        AI requests add_expense.

    Second call:
        AI returns the final response.
    """

    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def chat(
        self,
        messages,
        tools=None,
        temperature=0.2,
        max_tokens=1000,
    ) -> AIResponse:

        self.calls.append(
            {
                "messages": messages,
                "tools": tools,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
        )

        # First AI response → request a tool
        if len(self.calls) == 1:
            return AIResponse(
                content=None,
                tool_calls=[
                    ToolCallRequest(
                        name="add_expense",
                        arguments={
                            "amount": "850.00",
                            "category": "GROCERIES",
                            "expense_date": date.today().isoformat(),
                            "description": "Groceries",
                        },
                        call_id="call_add_expense_1",
                    )
                ],
            )

        # Second AI response → final answer
        return AIResponse(
            content=(
                "Your ₹850 grocery expense has been "
                "recorded successfully."
            ),
            tool_calls=[],
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_ai_to_tool_to_database_flow():
    """
    Verify:

    Mock AI
        ↓
    FamilyContextAgent
        ↓
    ToolRegistry
        ↓
    ExpenseService
        ↓
    ExpenseRepository
        ↓
    PostgreSQL
        ↓
    Tool result
        ↓
    Mock AI
        ↓
    Final response
    """

    async with AsyncSessionLocal() as session:

        family_id = uuid4()

        family = Family(
            id=family_id,
            name="Team 4 AI Test Family",
            timezone="Asia/Kolkata",
        )

        session.add(family)
        await session.commit()

        try:
            # -----------------------------------------
            # REAL BACKEND SERVICES
            # -----------------------------------------

            expense_repository = ExpenseRepository(session)

            expense_service = ExpenseService(
                expense_repository
            )

            commitment_repository = CommitmentRepository(session)

            commitment_service = CommitmentService(
                commitment_repository
            )

            # Real Tool Registry
            registry = ToolRegistry(
                expense_service=expense_service,
                commitment_service=commitment_service,
            )

            # Fake AI
            mock_ai = MockAIClient()

            # -----------------------------------------
            # REAL AGENT
            # -----------------------------------------
            #
            # cast() is only for the type checker.
            # It does NOT call NVIDIA.
            #
            agent = FamilyContextAgent(
                ai_client=cast(AIModelClient, mock_ai),
                tool_registry=registry,
            )

            # -----------------------------------------
            # AGENT STATE
            # -----------------------------------------

            state = AgentState(
                family_id=family_id,
                user_id=None,
                conversation_id=None,
                user_message="I spent ₹850 on groceries.",
            )

            # -----------------------------------------
            # RUN AGENT
            # -----------------------------------------

            result = await agent.run(state)

            # =========================================
            # 1. FINAL AI RESPONSE
            # =========================================

            assert result.assistant_message == (
                "Your ₹850 grocery expense has been "
                "recorded successfully."
            )

            # =========================================
            # 2. TOOL CALL WAS RECORDED
            # =========================================

            assert len(result.tool_calls) == 1

            assert result.tool_calls[0]["name"] == "add_expense"

            assert result.tool_calls[0]["arguments"]["family_id"] == str(
                family_id
            )

            # =========================================
            # 3. TOOL RESULT WAS RECORDED
            # =========================================

            assert len(result.tool_results) == 1

            tool_result = result.tool_results[0]["result"]

            assert tool_result["success"] is True

            assert tool_result["message"] == "Expense recorded"

            assert tool_result["expense_id"]

            # =========================================
            # 4. AI WAS CALLED TWICE
            # =========================================

            assert len(mock_ai.calls) == 2

            # =========================================
            # 5. SECOND AI CALL RECEIVED TOOL RESULT
            # =========================================

            second_call_messages = mock_ai.calls[1]["messages"]

            tool_messages = [
                message
                for message in second_call_messages
                if message.get("role") == "tool"
            ]

            assert len(tool_messages) == 1

            assert "expense_id" in tool_messages[0]["content"]

            assert "success" in tool_messages[0]["content"]

            # =========================================
            # 6. AI RECEIVED TOOL DEFINITIONS
            # =========================================

            first_call_tools = mock_ai.calls[0]["tools"]

            assert first_call_tools is not None

            tool_names = {
                tool["function"]["name"]
                for tool in first_call_tools
            }

            assert "add_expense" in tool_names

            # All 7 registered tools should be available
            assert len(tool_names) == 7

            # =========================================
            # 7. VERIFY REAL POSTGRESQL DATA
            # =========================================

            expense_id = tool_result["expense_id"]

            stored_expense = await session.scalar(
                select(Expense).where(
                    Expense.id == expense_id
                )
            )

            assert stored_expense is not None

            assert stored_expense.family_id == family_id

            assert stored_expense.amount == 850

            assert stored_expense.category == "GROCERIES"

            assert stored_expense.description == "Groceries"

            assert stored_expense.expense_date == date.today()

            # =========================================
            # OUTPUT
            # =========================================

            print("\n========================================")
            print("AI → AGENT → TOOL → DATABASE TEST PASSED")
            print("========================================")
            print("Tool:", result.tool_calls[0]["name"])
            print("Amount:", stored_expense.amount)
            print("Category:", stored_expense.category)
            print("Assistant:", result.assistant_message)
            print("========================================")

        finally:
            # -----------------------------------------
            # CLEAN UP TEST DATA
            # -----------------------------------------

            await session.execute(
                delete(Expense).where(
                    Expense.family_id == family_id
                )
            )

            await session.execute(
                delete(Family).where(
                    Family.id == family_id
                )
            )

            await session.commit()