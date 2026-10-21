"""Database access for conversations and their messages."""
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
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

    async def add_message(
        self,
        conversation_id: UUID,
        role: str,
        content: str,
    ) -> Message:
        """Persist a message with a chronological sequence per conversation."""

        # Lock the parent conversation so concurrent message writes
        # cannot allocate the same next sequence number.
        conversation = await self._session.scalar(
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .with_for_update()
        )

        if conversation is None:
            raise ValueError(
                f"Conversation {conversation_id} does not exist."
            )

        current_max = await self._session.scalar(
            select(func.coalesce(func.max(Message.sequence_number), 0))
            .where(Message.conversation_id == conversation_id)
        )

        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            created_at=datetime.now(timezone.utc),
            sequence_number=int(current_max or 0) + 1,
        )

        self._session.add(message)
        await self._session.flush()
        await self._session.refresh(message)

        return message

    async def recent_messages(
        self,
        conversation_id: UUID,
        limit: int,
    ) -> list[Message]:
        """Return the latest messages in chronological order."""

        if limit <= 0:
            return []

        statement = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.sequence_number.desc())
            .limit(limit)
        )

        messages = list(
            (await self._session.scalars(statement)).all()
        )

        messages.reverse()
        return messages

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
