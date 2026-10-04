"""
Schemas used by the Family Context Agent and Chat API.
"""

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request sent by the Family Context Agent."""

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
    arguments: dict[str, Any] = Field(default_factory=dict)


class Clarification(BaseModel):
    """A question the agent asks when required information is missing."""

    question: str = Field(min_length=1, max_length=500)
    missing_fields: list[str] = Field(default_factory=list)
    reason: str | None = None


class AgentDecision(BaseModel):
    """Decision made by the agent before executing a tool."""

    action: Literal["tool_call", "clarification", "response"]

    tool_call: ToolCall | None = None
    clarification: Clarification | None = None
    response: str | None = None

    @classmethod
    def tool(
        cls,
        name: str,
        arguments: dict[str, Any],
    ) -> "AgentDecision":
        return cls(
            action="tool_call",
            tool_call=ToolCall(
                name=name,
                arguments=arguments,
            ),
        )

    @classmethod
    def ask(
        cls,
        question: str,
        missing_fields: list[str] | None = None,
        reason: str | None = None,
    ) -> "AgentDecision":
        return cls(
            action="clarification",
            clarification=Clarification(
                question=question,
                missing_fields=missing_fields or [],
                reason=reason,
            ),
        )

    @classmethod
    def answer(cls, response: str) -> "AgentDecision":
        return cls(
            action="response",
            response=response,
        )


class AgentContext(BaseModel):
    """Context available to the Family Context Agent."""

    family_id: UUID
    user_id: UUID | None = None
    conversation_id: UUID | None = None
    message: str = ""
    history: list[dict[str, Any]] = Field(default_factory=list)


class ChatResponse(BaseModel):
    """Response returned by the Chat API."""

    message: str | None = None

    conversation_id: UUID | None = None

    tool_calls: list[ToolCall] = Field(default_factory=list)

    requires_clarification: bool = False

    metadata: dict[str, Any] = Field(default_factory=dict)