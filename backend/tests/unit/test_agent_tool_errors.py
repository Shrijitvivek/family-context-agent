from uuid import uuid4

import pytest

from app.agents.orchestrator import FamilyContextAgent
from app.agents.state import AgentState
from app.clients.ai_model import AIResponse, ToolCallRequest
from app.core.exceptions import DuplicateCommitmentError, ToolInputValidationError


class FakeAIClient:
    def __init__(self, tool_name: str, arguments: dict) -> None:
        self.tool_name = tool_name
        self.arguments = arguments
        self.calls = 0

    async def chat(self, **_kwargs):
        self.calls += 1
        if self.calls == 1:
            return AIResponse(
                content=None,
                tool_calls=[
                    ToolCallRequest(
                        name=self.tool_name,
                        arguments=self.arguments,
                        call_id="call-1",
                    )
                ],
            )
        return AIResponse(content="I need to clarify that request.", tool_calls=[])


class FakeToolRegistry:
    def __init__(self, error: Exception) -> None:
        self.error = error
        self.dispatched: list[tuple[str, dict]] = []

    def definitions(self) -> list[dict]:
        return []

    async def dispatch(self, name: str, arguments: dict) -> dict:
        self.dispatched.append((name, dict(arguments)))
        raise self.error


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error",
    [
        DuplicateCommitmentError([{"commitment_id": "candidate-1"}]),
        ToolInputValidationError("Invalid input for add_expense"),
    ],
)
async def test_agent_run_records_tool_errors_and_keeps_conversation_flow(error) -> None:
    family_id = uuid4()
    registry = FakeToolRegistry(error)
    ai = FakeAIClient("create_commitment", {"title": "Electricity bill"})
    agent = FamilyContextAgent(ai, registry)  # type: ignore[arg-type]
    state = AgentState(
        family_id=family_id,
        user_id=uuid4(),
        conversation_id=uuid4(),
        user_message="Add the electricity bill",
    )

    result = await agent.run(state)

    assert registry.dispatched[0][1]["family_id"] == str(family_id)
    assert result.tool_results[0]["result"] == {
        "success": False,
        "error": str(error),
    }
    assert result.assistant_message == "I need to clarify that request."
    assert ai.calls == 2


@pytest.mark.asyncio
async def test_agent_does_not_dispatch_when_ai_returns_no_tool_call() -> None:
    class NoToolAI:
        async def chat(self, **_kwargs):
            from app.clients.ai_model import AIResponse

            return AIResponse(content="Please provide more detail.", tool_calls=[])

    registry = FakeToolRegistry(ToolInputValidationError("unused"))
    agent = FamilyContextAgent(NoToolAI(), registry)  # type: ignore[arg-type]
    state = AgentState(
        family_id=uuid4(),
        user_id=None,
        conversation_id=None,
        user_message="Add that bill",
    )

    result = await agent.run(state)

    assert result.assistant_message == "Please provide more detail."
    assert result.tool_calls == []
    assert registry.dispatched == []
