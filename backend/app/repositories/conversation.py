# """Conversation repository.

# TODO:
# - Persist conversations and messages.
# - Retrieve only the bounded recent context required by the agent.
# """


from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation


class ConversationRepository:
    """Database operations for conversations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        family_id: UUID,
    ) -> Conversation:

        conversation = Conversation(
            family_id=family_id,
        )

        self.session.add(conversation)

        await self.session.flush()
        await self.session.refresh(conversation)

        return conversation

    async def get_by_id(
        self,
        conversation_id: UUID,
    ) -> Conversation | None:

        result = await self.session.execute(
            select(Conversation)
            .where(Conversation.id == conversation_id)
        )

        return result.scalar_one_or_none()

    async def get_by_family(
        self,
        family_id: UUID,
    ) -> list[Conversation]:

        result = await self.session.execute(
            select(Conversation)
            .where(Conversation.family_id == family_id)
            .order_by(Conversation.updated_at.desc())
        )

        return list(result.scalars().all())