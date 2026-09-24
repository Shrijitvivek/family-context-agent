"""
Repository for observable agent events.
"""

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_event import AgentEvent


class AgentEventRepository:

    def __init__(
        self,
        db: AsyncSession,
    ) -> None:

        self.db = db

    async def create(
        self,
        *,
        family_id: UUID,
        event_type: str,
        conversation_id: UUID | None = None,
        tool_name: str | None = None,
        success: bool = True,
        latency_ms: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> AgentEvent:

        event = AgentEvent(
            family_id=family_id,
            conversation_id=conversation_id,
            event_type=event_type,
            tool_name=tool_name,
            success=success,
            latency_ms=latency_ms,
            details=details or {},
        )

        self.db.add(event)

        await self.db.flush()

        return event