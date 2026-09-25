from uuid import uuid4

import pytest

from app.agents.clarification import (
    build_clarification,
    find_missing_fields,
)
from app.agents.orchestrator import FamilyContextOrchestrator
from app.schemas.agent import AgentContext
from app.tools.registry import ToolRegistry


def test_expense_requires_amount_category_and_date() -> None:
    missing = find_missing_fields(
        "add_expense",
        {
            "amount": 500,
        },
    )

    assert missing == [
        "category",
        "expense_date",
    ]


def test_complete_expense_does_not_need_clarification() -> None:
    clarification = build_clarification(
        "add_expense",
        {
            "amount": 500,
            "category": "groceries",
            "expense_date": "2026-09-25",
        },
    )

    assert clarification is None


def test_missing_expense_category_returns_question() -> None:
    decision = build_clarification(
        "add_expense",
        {
            "amount": 500,
            "expense_date": "2026-09-25",
        },
    )

    assert decision is not None
    assert decision.action == "clarification"
    assert decision.clarification is not None
    assert decision.clarification.question == "What was the expense for?"


def test_commitment_requires_type_and_title() -> None:
    missing = find_missing_fields(
        "create_commitment",
        {},
    )

    assert missing == [
        "commitment_type",
        "title",
    ]


def test_complete_commitment_does_not_need_clarification() -> None:
    decision = build_clarification(
        "create_commitment",
        {
            "commitment_type": "BILL",
            "title": "Electricity bill",
        },
    )

    assert decision is None


def test_update_requires_commitment_id() -> None:
    decision = build_clarification(
        "update_commitment",
        {
            "status": "COMPLETED",
        },
    )

    assert decision is not None
    assert decision.action == "clarification"
    assert decision.clarification is not None


def test_dependency_requires_two_commitments() -> None:
    missing = find_missing_fields(
        "create_dependency",
        {
            "relationship_type": "MUST_COMPLETE_BEFORE",
        },
    )

    assert missing == [
        "source_commitment_id",
        "target_commitment_id",
    ]