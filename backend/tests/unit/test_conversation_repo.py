import uuid

import pytest

from app.db.Session import AsyncSessionLocal
from app.models.family import Family
from app.repositories.conversation_repository import (
    ConversationRepository,
)
from app.repositories.message_repository import (
    MessageRepository,
)


@pytest.mark.asyncio
async def test_conversation_and_messages():

    async with AsyncSessionLocal() as session:

        family = Family(
            name=f"Conversation Test {uuid.uuid4()}",
            timezone="Asia/Kolkata",
        )

        session.add(family)
        await session.flush()

        conversation_repo = ConversationRepository(session)
        message_repo = MessageRepository(session)

        # CREATE CONVERSATION
        conversation = await conversation_repo.create(
            family.id
        )

        assert conversation.id is not None

        # CREATE USER MESSAGE
        user_message = await message_repo.create(
            conversation_id=conversation.id,
            role="user",
            content="I need to pay my electricity bill.",
        )

        # CREATE ASSISTANT MESSAGE
        assistant_message = await message_repo.create(
            conversation_id=conversation.id,
            role="assistant",
            content="When is the bill due?",
        )

        assert user_message.id is not None
        assert assistant_message.id is not None

        # READ
        messages = await message_repo.get_by_conversation(
            conversation.id
        )

        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[1].role == "assistant"

        await session.rollback()