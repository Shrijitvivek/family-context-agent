"""
Repository for observable agent events.
"""

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_event import AgentEvent


class AgentEventRepository:
    """Persists observable Family Context Agent events."""

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
        description: str | None = None,
        event_data: dict[str, Any] | None = None,
    ) -> AgentEvent:
        """
        Create and flush one agent event.

        The event structure follows the Team 1
        agent_events database model.
        """

        event = AgentEvent(
            family_id=family_id,
            event_type=event_type,
            description=description,
            event_data=event_data or {},
        )

        self.db.add(event)

        await self.db.flush()

        return event