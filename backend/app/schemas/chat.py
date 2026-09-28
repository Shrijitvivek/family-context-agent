"""Chat request and response shapes."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ChatRequest(BaseModel):
    family_id: UUID
    member_id: UUID | None = None
    conversation_id: UUID | None = None
    message: str = Field(min_length=1, max_length=4_000)

    @field_validator("message")
    @classmethod
    def strip_message(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("message cannot be blank")
        return value


class ChatResponse(BaseModel):
    conversation_id: UUID
    action: Literal["tool_call", "clarification", "response", "error"]
    reply: str
    tool_name: str | None = None
    tool_result: dict[str, Any] | None = None
    missing_fields: list[str] = Field(default_factory=list)


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    role: str
    content: str
    created_at: datetime
