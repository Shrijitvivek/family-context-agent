from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message


class MessageRepository:
    """Database operations for messages."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        conversation_id: UUID,
        role: str,
        content: str,
    ) -> Message:

        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
        )

        self.session.add(message)

        await self.session.flush()
        await self.session.refresh(message)

        return message

    async def get_by_id(
        self,
        message_id: UUID,
    ) -> Message | None:

        result = await self.session.execute(
            select(Message)
            .where(Message.id == message_id)
        )

        return result.scalar_one_or_none()

    async def get_by_conversation(
        self,
        conversation_id: UUID,
    ) -> list[Message]:

        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )

        return list(result.scalars().all())

    async def get_recent(
        self,
        conversation_id: UUID,
        limit: int = 20,
    ) -> list[Message]:

        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )

        messages = list(result.scalars().all())

        return list(reversed(messages))