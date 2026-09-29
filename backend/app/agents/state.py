from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass
class AgentState:
    """State maintained during one Family Context Agent interaction."""

    family_id: UUID
    user_id: UUID | None
    conversation_id: UUID | None

    user_message: str

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