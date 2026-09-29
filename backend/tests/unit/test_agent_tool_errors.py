"""Tests for member_id handling and for tool errors turned into clarifications."""

from typing import Any
from uuid import uuid4

import pytest

from app.agents.orchestrator import FamilyContextOrchestrator
from app.core.exceptions import DuplicateCommitmentError, ToolInputValidationError
from app.schemas.agent import AgentContext, AgentDecision

TOOL_NAMES = (
    "add_expense",
    "get_expense_summary",
    "create_commitment",
    "search_commitments",
    "update_commitment",
    "create_dependency",
    "get_family_priorities",
)


class FakeToolRegistry:
    """Same interface as ToolRegistry. Can be told to raise an error."""

    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.dispatched: list[tuple[str, dict[str, Any]]] = []

    @property
    def names(self) -> tuple[str, ...]:
        return TOOL_NAMES

    def definitions(self) -> list[dict[str, Any]]:
        return []

    async def dispatch(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        self.dispatched.append((name, dict(arguments)))
        if self.error is not None:
            raise self.error
        return {"success": True}


@pytest.fixture
def context() -> AgentContext:
    return AgentContext(family_id=uuid4(), member_id=uuid4())


# ---------- member_id ----------


@pytest.mark.asyncio
async def test_household_summary_is_not_filtered_to_speaker(context) -> None:
    registry = FakeToolRegistry()
    orchestrator = FamilyContextOrchestrator(registry)

    await orchestrator.handle_decision(
        AgentDecision.tool("get_expense_summary", {}), context
    )

    arguments = registry.dispatched[0][1]
    assert "member_id" not in arguments
    assert arguments["family_id"] == str(context.family_id)


@pytest.mark.asyncio
async def test_new_expense_belongs_to_speaker(context) -> None:
    registry = FakeToolRegistry()
    orchestrator = FamilyContextOrchestrator(registry)

    await orchestrator.handle_decision(
        AgentDecision.tool(
            "add_expense",
            {"amount": 500, "category": "groceries", "expense_date": "2026-09-27"},
        ),
        context,
    )

    assert registry.dispatched[0][1]["member_id"] == str(context.member_id)


# ---------- tool errors become clarifications ----------


@pytest.mark.asyncio
async def test_duplicate_commitment_asks_user(context) -> None:
    candidates = [{"commitment_id": str(uuid4())}]
    registry = FakeToolRegistry(error=DuplicateCommitmentError(candidates))
    orchestrator = FamilyContextOrchestrator(registry)

    result = await orchestrator.handle_decision(
        AgentDecision.tool(
            "create_commitment",
            {"commitment_type": "BILL", "title": "Electricity Bill"},
        ),
        context,
    )

    assert result.decision.action == "clarification"
    assert result.tool_result is not None
    assert result.tool_result["error"] == "possible_duplicate_commitment"
    assert result.tool_result["candidates"] == candidates


@pytest.mark.asyncio
async def test_invalid_tool_input_asks_user(context) -> None:
    error = ToolInputValidationError(
        "Invalid input for 'add_expense'.",
        details={
            "tool_name": "add_expense",
            "errors": [{"loc": ("amount",), "msg": "Input should be greater than 0"}],
        },
    )
    registry = FakeToolRegistry(error=error)
    orchestrator = FamilyContextOrchestrator(registry)

    result = await orchestrator.handle_decision(
        AgentDecision.tool(
            "add_expense",
            {"amount": 0, "category": "groceries", "expense_date": "2026-09-27"},
        ),
        context,
    )

    assert result.decision.action == "clarification"
    assert result.decision.clarification is not None
    assert result.decision.clarification.missing_fields == ["amount"]
    assert result.tool_result == {"error": "invalid_tool_input", "fields": ["amount"]}