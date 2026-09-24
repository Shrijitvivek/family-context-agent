"""
State maintained during one Family Context Agent request.
"""

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass
class AgentState:

    family_id: UUID

    user_id: UUID | None

    user_message: str

    conversation_id: UUID | None = None

    assistant_message: str = ""

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

    clarification_question: str | None = None