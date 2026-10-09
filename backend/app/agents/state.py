from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass
class AgentState:
    """State maintained during one Family Context Agent interaction."""

    family_id: UUID
    member_id: UUID | None
    conversation_id: UUID | None

    user_message: str

    # Current household state retrieved from PostgreSQL.
    household_context: str | None = None

    history: list[dict[str, str]] = field(default_factory=list)

    assistant_message: str | None = None

    tool_calls: list[dict[str, Any]] = field(
        default_factory=list
    )

    tool_results: list[dict[str, Any]] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    requires_clarification: bool = False

    assistant_message: str | None = None

    tool_calls: list[dict[str, Any]] = field(
        default_factory=list
    )

    tool_results: list[dict[str, Any]] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    requires_clarification: bool = False
