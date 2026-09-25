from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.conversation_repository import (
    ConversationRepository,
)
from app.repositories.message_repository import MessageRepository


class ConversationService:
    """Business logic for conversations and messages."""

    def __init__(self, session: AsyncSession):
        self.conversation_repository = ConversationRepository(session)
        self.message_repository = MessageRepository(session)
        self.session = session

    async def create_conversation(
        self,
        family_id: UUID,
    ):

        conversation = await self.conversation_repository.create(
            family_id
        )

        await self.session.commit()

        return conversation

    async def get_conversation(
        self,
        conversation_id: UUID,
    ):

        return await self.conversation_repository.get_by_id(
            conversation_id
        )

    async def get_family_conversations(
        self,
        family_id: UUID,
    ):

        return await self.conversation_repository.get_by_family(
            family_id
        )

    async def add_message(
        self,
        conversation_id: UUID,
        role: str,
        content: str,
    ):

        if not content.strip():
            raise ValueError("Message content cannot be empty.")

        message = await self.message_repository.create(
            conversation_id=conversation_id,
            role=role,
            content=content,
        )

        await self.session.commit()

        return message

    async def get_messages(
        self,
        conversation_id: UUID,
    ):

        return await self.message_repository.get_by_conversation(
            conversation_id
        )

    async def get_recent_messages(
        self,
        conversation_id: UUID,
        limit: int = 20,
    ):

        return await self.message_repository.get_recent(
            conversation_id,
            limit,
        )