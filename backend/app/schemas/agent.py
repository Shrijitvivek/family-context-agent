"""
Schemas used by the Team 4 AI/chat integration.
"""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):

    family_id: UUID

    user_id: UUID | None = None

    message: str = Field(
        min_length=1,
        max_length=5000,
    )

    conversation_id: UUID | None = None


class ToolCall(BaseModel):

    name: str

    arguments: dict[str, Any] = Field(
        default_factory=dict
    )


class ChatResponse(BaseModel):

    message: str

    conversation_id: UUID | None = None

    tool_calls: list[ToolCall] = Field(
        default_factory=list
    )

    requires_clarification: bool = False

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )