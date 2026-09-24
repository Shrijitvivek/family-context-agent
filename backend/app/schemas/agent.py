"""
Schemas used by the Family Context Agent and Chat API.
"""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request sent to the Family Context Agent."""

    family_id: UUID
    user_id: UUID | None = None
    conversation_id: UUID | None = None

    message: str = Field(
        min_length=1,
        description="Message sent by the family member.",
    )


class ToolCall(BaseModel):
    """A tool requested by the AI agent."""

    name: str

    arguments: dict[str, Any] = Field(
        default_factory=dict
    )


class ChatResponse(BaseModel):
    """Response returned by the Chat API."""

    message: str | None = None

    conversation_id: UUID | None = None

    tool_calls: list[ToolCall] = Field(
        default_factory=list
    )

    requires_clarification: bool = False

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )