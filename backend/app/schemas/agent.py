"""Structured schemas used by the Family Context Agent."""

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    """A validated request from the model to call one registered tool."""

    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class Clarification(BaseModel):
    """A question the agent must ask before taking an action."""

    question: str = Field(min_length=1, max_length=500)
    missing_fields: list[str] = Field(default_factory=list)
    reason: str | None = None


class AgentDecision(BaseModel):
    """The model's high-level decision."""

    action: Literal["tool_call", "clarification", "response"]

    tool_call: ToolCall | None = None
    clarification: Clarification | None = None
    response: str | None = None

    @classmethod
    def tool(cls, name: str, arguments: dict[str, Any]) -> "AgentDecision":
        return cls(
            action="tool_call",
            tool_call=ToolCall(
                tool_name=name,
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
    """Information available to the agent for the current turn."""

    family_id: UUID
    member_id: UUID | None = None
    conversation_id: UUID | None = None

    # Information extracted from the current/previous conversation.
    extracted: dict[str, Any] = Field(default_factory=dict)


class AgentTurnResult(BaseModel):
    """Safe result returned by the orchestrator."""

    decision: AgentDecision
    tool_result: dict[str, Any] | None = None