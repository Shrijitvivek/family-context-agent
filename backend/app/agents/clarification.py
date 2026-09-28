"""Rules for deciding when the Family Context Agent needs clarification."""

from typing import Any

from app.schemas.agent import AgentDecision


# Fields that are required before each state-changing tool can be used.
REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    "add_expense": (
        "amount",
        "category",
        "expense_date",
    ),
    "create_commitment": (
        "commitment_type",
        "title",
    ),
    "update_commitment": (
        "commitment_id",
    ),
    "create_dependency": (
        "source_commitment_id",
        "target_commitment_id",
        "relationship_type",
    ),
}


FIELD_QUESTIONS: dict[str, str] = {
    "amount": "What was the amount of the expense?",
    "category": "What was the expense for?",
    "expense_date": "What date was the expense made?",
    "commitment_type": (
        "What type of commitment is this "
        "(for example, bill, appointment, task, or deadline)?"
    ),
    "title": "What should I call this commitment?",
    "commitment_id": "Which commitment would you like to update?",
    "source_commitment_id": "Which commitment must be completed first?",
    "target_commitment_id": "Which commitment depends on it?",
    "relationship_type": "What is the relationship between the two commitments?",
}


def find_missing_fields(
    tool_name: str,
    arguments: dict[str, Any],
) -> list[str]:
    """Return required fields that have not been supplied."""

    required = REQUIRED_FIELDS.get(tool_name, ())

    missing: list[str] = []

    for field in required:
        value = arguments.get(field)

        if value is None:
            missing.append(field)
            continue

        if isinstance(value, str) and not value.strip():
            missing.append(field)

    return missing


def build_clarification(
    tool_name: str,
    arguments: dict[str, Any],
) -> AgentDecision | None:
    """Return a clarification decision if the tool call is incomplete."""

    missing = find_missing_fields(tool_name, arguments)

    if not missing:
        return None

    # Ask only one focused question at a time.
    field = missing[0]

    question = FIELD_QUESTIONS.get(
        field,
        f"Could you provide the {field.replace('_', ' ')}?",
    )

    return AgentDecision.ask(
        question=question,
        missing_fields=missing,
        reason=f"{tool_name} is missing required information.",
    )