"""Chat and agent interaction schemas.

TODO:
- Define message requests and assistant responses.
- Include structured intent, clarification options, confirmations, and safe UI actions.
"""
"""Chat request and response schemas."""

from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    family_id: UUID
    user_id: UUID | None = None
    conversation_id: UUID | None = None
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    conversation_id: UUID | None
    message: str
    tool_calls: list[dict] = Field(default_factory=list)
    tool_results: list[dict] = Field(default_factory=list)
    requires_clarification: bool = False