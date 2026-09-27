from datetime import date
from typing import cast
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import delete, select

from app.api.dependencies import get_ai_client
from app.db.session import AsyncSessionLocal
from app.main import app
from app.models.agent_event import AgentEvent
from app.models.expense import Expense
from app.models.family import Family
from app.clients.ai_model import AIModelClient, AIResponse, ToolCallRequest


class MockAIClient:
    """
    Fake AI client used for Chat API integration testing.

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
async def test_chat_api_end_to_end():
    """
    Verify the complete HTTP/API flow:

    HTTP POST /api/v1/chat
        ↓
    FastAPI
        ↓
    ChatService
        ↓
    FamilyContextAgent
        ↓
    Mock AI
        ↓
    Tool Registry
        ↓
    PostgreSQL
        ↓
    Agent Events
        ↓
    ChatResponse
    """

    family_id = uuid4()
    mock_ai = MockAIClient()

    # -----------------------------------------
    # Override ONLY the AI dependency.
    #
    # This prevents any NVIDIA API call.
    # Database-backed dependencies remain real.
    # -----------------------------------------

    app.dependency_overrides[get_ai_client] = (
        lambda: cast(AIModelClient, mock_ai)
    )

    async with AsyncSessionLocal() as session:

        family = Family(
            id=family_id,
            name="Team 4 Chat API Test Family",
            timezone="Asia/Kolkata",
        )

        session.add(family)
        await session.commit()

        try:
            # -----------------------------------------
            # CREATE REAL HTTP CLIENT FOR FASTAPI
            # -----------------------------------------

            transport = httpx.ASGITransport(
                app=app
            )

            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://test",
            ) as client:

                response = await client.post(
                    "/api/v1/chat",
                    json={
                        "family_id": str(family_id),
                        "user_id": None,
                        "conversation_id": None,
                        "message": "I spent ₹850 on groceries.",
                    },
                )

            # =========================================
            # 1. HTTP RESPONSE
            # =========================================

            assert response.status_code == 200

            response_data = response.json()

            # =========================================
            # 2. FINAL CHAT RESPONSE
            # =========================================

            assert response_data["message"] == (
                "Your ₹850 grocery expense has "
                "been recorded successfully."
            )

            # =========================================
            # 3. TOOL CALL IN API RESPONSE
            # =========================================

            assert len(response_data["tool_calls"]) == 1

            assert (
                response_data["tool_calls"][0]["name"]
                == "add_expense"
            )

            # =========================================
            # 4. TOOL RESULT IN API METADATA
            # =========================================

            tool_results = response_data["metadata"]["tool_results"]

            assert len(tool_results) == 1

            tool_result = tool_results[0]["result"]

            assert tool_result["success"] is True
            assert tool_result["message"] == "Expense recorded"
            assert tool_result["expense_id"]

            # =========================================
            # 5. VERIFY REAL DATABASE WRITE
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
            # 7. VERIFY AI WAS CALLED TWICE
            # =========================================

            assert len(mock_ai.calls) == 2

            # =========================================
            # OUTPUT
            # =========================================

            print("\n========================================")
            print("CHAT API INTEGRATION TEST PASSED")
            print("========================================")
            print("Endpoint: POST /api/v1/chat")
            print("Status:", response.status_code)
            print("Tool:", response_data["tool_calls"][0]["name"])
            print("Amount:", stored_expense.amount)
            print("Category:", stored_expense.category)
            print("Events:", event_types)
            print("Response:", response_data["message"])
            print("========================================")

        finally:
            # -----------------------------------------
            # CLEANUP
            # -----------------------------------------

            app.dependency_overrides.pop(
                get_ai_client,
                None,
            )

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