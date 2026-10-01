"""Agent event repository.

TODO:
- Persist observable agent and tool events for debugging and evaluation.
- Support request, conversation, entity, event-type, and time filters.
"""
"""Persistence for observable agent and tool events."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_event import AgentEvent


class AgentEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(
        self,
        family_id: UUID,
        event_type: str,
        description: str | None = None,
        event_data: dict | None = None,
    ) -> AgentEvent:
        event = AgentEvent(
            family_id=family_id,
            event_type=event_type,
            description=description,
            event_data=event_data,
        )
        self._session.add(event)
        await self._session.flush()
        return event

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()

    async def list_by_family(
        self,
        family_id: UUID,
        limit: int = 100,
    ) -> list[AgentEvent]:
        statement = (
            select(AgentEvent)
            .where(AgentEvent.family_id == family_id)
            .order_by(AgentEvent.created_at.desc())
            .limit(limit)
        )
        result = await self._session.scalars(statement)
        return list(result.all())