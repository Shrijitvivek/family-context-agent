from datetime import date
from typing import cast
from uuid import uuid4

import pytest
from sqlalchemy import delete, select

from app.clients.ai_model import AIModelClient, AIResponse, ToolCallRequest
from app.db.session import AsyncSessionLocal
from app.models.agent_event import AgentEvent
from app.models.expense import Expense
from app.models.family import Family
from app.repositories.agent_event import AgentEventRepository
from app.repositories.commitment import CommitmentRepository
from app.repositories.expense import ExpenseRepository
from app.services.chat import ChatService
from app.services.commitment import CommitmentService
from app.services.expense import ExpenseService
from app.tools.registry import ToolRegistry


class MockAIClient:
    """
    Fake AI client used for ChatService integration testing.

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

        # -----------------------------------------
        # FIRST AI CALL
        # -----------------------------------------

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

        # -----------------------------------------
        # SECOND AI CALL
        # -----------------------------------------

        return AIResponse(
            content=(
                "Your ₹850 grocery expense has "
                "been recorded successfully."
            ),
            tool_calls=[],
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_chat_service_end_to_end():
    """
    Verify the ChatService flow:

    ChatService
        ↓
    FamilyContextAgent
        ↓
    Mock AI
        ↓
    Tool Registry
        ↓
    Expense Service
        ↓
    PostgreSQL
        ↓
    Agent Events
        ↓
    ChatService response
    """

    async with AsyncSessionLocal() as session:

        family_id = uuid4()

        family = Family(
            id=family_id,
            name="Team 4 Chat Test Family",
            timezone="Asia/Kolkata",
        )

        session.add(family)
        await session.commit()

        try:
            # =========================================
            # REAL REPOSITORIES
            # =========================================

            expense_repository = ExpenseRepository(session)

            commitment_repository = CommitmentRepository(session)

            agent_event_repository = AgentEventRepository(session)

            # =========================================
            # REAL SERVICES
            # =========================================

            expense_service = ExpenseService(
                expense_repository
            )

            commitment_service = CommitmentService(
                commitment_repository
            )

            # =========================================
            # REAL TOOL REGISTRY
            # =========================================

            registry = ToolRegistry(
                expense_service=expense_service,
                commitment_service=commitment_service,
            )

            # =========================================
            # MOCK AI
            # =========================================

            mock_ai = MockAIClient()

            # =========================================
            # REAL CHAT SERVICE
            # =========================================

            chat_service = ChatService(
                ai_client=cast(AIModelClient, mock_ai),
                tool_registry=registry,
                agent_event_repository=agent_event_repository,
            )

            # =========================================
            # RUN CHAT SERVICE
            # =========================================

            state = await chat_service.process_message(
                family_id=family_id,
                user_id=None,
                conversation_id=None,
                message="I spent ₹850 on groceries.",
            )

            # =========================================
            # 1. FINAL RESPONSE
            # =========================================

            assert state.assistant_message == (
                "Your ₹850 grocery expense has "
                "been recorded successfully."
            )

            # =========================================
            # 2. TOOL WAS USED
            # =========================================

            assert len(state.tool_calls) == 1
            assert state.tool_calls[0]["name"] == "add_expense"

            # =========================================
            # 3. TOOL RESULT EXISTS
            # =========================================

            assert len(state.tool_results) == 1

            tool_result = state.tool_results[0]["result"]

            assert tool_result["success"] is True
            assert tool_result["message"] == "Expense recorded"
            assert tool_result["expense_id"]

            # =========================================
            # 4. VERIFY EXPENSE IN POSTGRESQL
            # =========================================

            stored_expense = await session.scalar(
                select(Expense).where(
                    Expense.family_id == family_id
                )
            )

            assert stored_expense is not None
            assert stored_expense.amount == 850
            assert stored_expense.category == "GROCERIES"
            assert stored_expense.description == "Groceries"
            assert stored_expense.expense_date == date.today()

            # =========================================
            # 5. VERIFY AI CALLED TWICE
            # =========================================

            assert len(mock_ai.calls) == 2

            # =========================================
            # 6. VERIFY AGENT EVENTS
            # =========================================

            events = (
                await session.scalars(
                    select(AgentEvent)
                    .where(
                        AgentEvent.family_id == family_id
                    )
                    .order_by(AgentEvent.created_at)
                )
            ).all()

            event_types = [
                event.event_type
                for event in events
            ]

            assert "agent_started" in event_types
            assert "agent_completed" in event_types
            assert len(events) == 2

            # =========================================
            # 7. VERIFY START EVENT
            # =========================================

            started_event = next(
                event
                for event in events
                if event.event_type == "agent_started"
            )

            assert started_event.family_id == family_id

            assert (
                started_event.description
                == "Family Context Agent started processing a message."
            )

            start_event_data = started_event.event_data or {}

            assert (
                start_event_data.get("message")
                == "I spent ₹850 on groceries."
            )

            assert start_event_data.get("user_id") is None
            assert start_event_data.get("conversation_id") is None

            # =========================================
            # 8. VERIFY COMPLETED EVENT
            # =========================================

            completed_event = next(
                event
                for event in events
                if event.event_type == "agent_completed"
            )

            assert completed_event.family_id == family_id

            assert (
                completed_event.description
                == "Family Context Agent completed successfully."
            )

            completed_event_data = (
                completed_event.event_data or {}
            )

            assert completed_event_data.get("tool_count") == 1

            # =========================================
            # OUTPUT
            # =========================================

            print("\n========================================")
            print("CHAT SERVICE INTEGRATION TEST PASSED")
            print("========================================")
            print("Message: I spent ₹850 on groceries.")
            print("Tool:", state.tool_calls[0]["name"])
            print("Amount:", stored_expense.amount)
            print("Category:", stored_expense.category)
            print("Events:", event_types)
            print("Response:", state.assistant_message)
            print("========================================")

        finally:
            # =========================================
            # CLEANUP
            # =========================================

            await session.execute(
                delete(AgentEvent).where(
                    AgentEvent.family_id == family_id
                )
            )

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