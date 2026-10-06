"""Database access for conversations and their messages."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.models.message import Message
from app.repositories.query import require_family_scope


class ConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, family_id: UUID, conversation_id: UUID) -> Conversation:
        conversation = await self._session.get(Conversation, conversation_id)
        return require_family_scope(conversation, family_id, "Conversation", conversation_id)

    async def create(self, family_id: UUID) -> Conversation:
        conversation = Conversation(family_id=family_id)
        self._session.add(conversation)
        await self._session.flush()
        return conversation

    async def add_message(self, conversation_id: UUID, role: str, content: str) -> Message:
        message = Message(conversation_id=conversation_id, role=role, content=content)
        self._session.add(message)
        await self._session.flush()
        await self._session.refresh(message)
        return message

    async def recent_messages(self, conversation_id: UUID, limit: int) -> list[Message]:
        """Return the latest ``limit`` messages, oldest first."""

        statement = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc(), Message.id.desc())
            .limit(limit)
        )
        messages = list((await self._session.scalars(statement)).all())
        messages.reverse()
        return messages

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
