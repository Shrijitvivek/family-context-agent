"""Chat and agent interaction schemas."""

from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    family_id: UUID
    member_id: UUID | None = None
    user_id: UUID | None = None
    conversation_id: UUID | None = None
    document_id: UUID | None = None
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    conversation_id: UUID | None
    message: str
    tool_calls: list[dict] = Field(default_factory=list)
    tool_results: list[dict] = Field(default_factory=list)
    requires_clarification: bool = False


class ChatHistoryMessage(BaseModel):
    id: UUID
    role: str
    content: str


class ChatHistoryResponse(BaseModel):
    conversation_id: UUID
    messages: list[ChatHistoryMessage] = Field(default_factory=list)