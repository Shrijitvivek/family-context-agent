from uuid import uuid4

import pytest

from app.agents.orchestrator import FamilyContextAgent
from app.agents.state import AgentState
from app.clients.ai_model import AIResponse, ToolCallRequest


class FakeAIClient:
    def __init__(self) -> None:
        self.calls: list[list[dict]] = []

    async def chat(self, *, messages, tools=None, **_kwargs):
        self.calls.append(messages)
        if len(self.calls) == 1:
            return AIResponse(
                content=None,
                tool_calls=[
                    ToolCallRequest(
                        name="add_expense",
                        arguments={
                            "amount": "850",
                            "category": "groceries",
                            "expense_date": "2026-10-08",
                        },
                        call_id="expense-call",
                    )
                ],
            )
        return AIResponse(content="Expense recorded.", tool_calls=[])


class RecordingRegistry:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def definitions(self) -> list[dict]:
        return [{"type": "function", "function": {"name": "add_expense"}}]

    async def dispatch(self, name: str, arguments: dict) -> dict:
        self.calls.append((name, dict(arguments)))
        return {"success": True, "expense_id": str(uuid4())}


@pytest.mark.asyncio
async def test_agent_tool_flow_uses_registry_and_returns_tool_result() -> None:
    family_id = uuid4()
    ai = FakeAIClient()
    registry = RecordingRegistry()
    agent = FamilyContextAgent(ai, registry)  # type: ignore[arg-type]
    state = AgentState(
        family_id=family_id,
        user_id=None,
        conversation_id=None,
        user_message="I spent 850 on groceries on 2026-10-08",
    )

    result = await agent.run(state)

    assert len(ai.calls) == 2
    assert registry.calls[0][0] == "add_expense"
    assert registry.calls[0][1]["family_id"] == str(family_id)
    assert result.tool_results[0]["result"]["success"] is True
    assert result.assistant_message == "Expense recorded."
    assert ai.calls[1][-1]["role"] == "tool"
