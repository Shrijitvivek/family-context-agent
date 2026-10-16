"""Deterministic real-PostgreSQL tests for conversation and reference safety."""

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import delete, select

from app.clients.ai_model import AIResponse, ToolCallRequest
from app.core.constants import CommitmentStatus, CommitmentType, Priority, SourceType
from app.db.session import AsyncSessionLocal
from app.models.commitment import Commitment
from app.models.conversation import Conversation
from app.models.expense import Expense
from app.models.family import Family
from app.models.family_member import FamilyMember
from app.models.message import Message
from app.models.agent_event import AgentEvent
from app.services.chat import ChatService


class ScriptedChatModel:
    """Return fixed responses and retain the exact prompt sent each turn."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    async def chat(self, *, messages, tools=None, **_kwargs):
        self.calls.append({"messages": messages, "tools": tools})
        return self.responses.pop(0)


def _tool(name, arguments, call_id):
    return AIResponse(
        content=None,
        tool_calls=[ToolCallRequest(name=name, arguments=arguments, call_id=call_id)],
    )


def _bill(family_id, member_id, title, due_date):
    return Commitment(
        id=uuid4(),
        family_id=family_id,
        member_id=member_id,
        commitment_type=CommitmentType.BILL.value,
        category="ELECTRICITY",
        title=title,
        description=title,
        amount=Decimal("3240.00"),
        due_date=due_date,
        status=CommitmentStatus.PENDING.value,
        priority=Priority.MEDIUM.value,
        source_type=SourceType.MANUAL.value,
    )


async def _cleanup(session, family_ids):
    await session.rollback()
    await session.execute(delete(Family).where(Family.id.in_(family_ids)))
    await session.commit()


@pytest.mark.asyncio(loop_scope="session")
async def test_chat_persists_and_reloads_history_with_family_scoped_context(monkeypatch):
    import app.services.chat as chat_module

    family_id, other_family_id = uuid4(), uuid4()
    member_id, sibling_id, other_member_id = uuid4(), uuid4(), uuid4()
    today = date(2026, 10, 13)
    first_commitment = _bill(family_id, member_id, "Electricity Bill", date(2026, 10, 18))
    second_commitment = _bill(family_id, sibling_id, "Internet Bill", date(2026, 10, 21))
    unrelated_commitment = _bill(other_family_id, other_member_id, "Secret Other Bill", date(2026, 10, 19))
    model = ScriptedChatModel([
        AIResponse(content="The electricity bill is due October 18.", tool_calls=[]),
        AIResponse(content="The electricity bill is still pending.", tool_calls=[]),
    ])
    monkeypatch.setattr(chat_module, "AIModelClient", lambda: model)

    async with AsyncSessionLocal() as session:
        session.add_all([
            Family(id=family_id, name="Context Family"),
            Family(id=other_family_id, name="Other Family"),
            FamilyMember(id=member_id, family_id=family_id, name="Rahul", relationship_type="PARENT"),
            FamilyMember(id=sibling_id, family_id=family_id, name="Maya", relationship_type="CHILD"),
            FamilyMember(id=other_member_id, family_id=other_family_id, name="Other", relationship_type="PARENT"),
            first_commitment, second_commitment, unrelated_commitment,
            Expense(family_id=family_id, member_id=member_id, amount=Decimal("55.00"), category="GROCERIES", expense_date=today),
            Expense(family_id=other_family_id, member_id=other_member_id, amount=Decimal("999.00"), category="SECRET", expense_date=today),
        ])
        await session.flush()
        try:
            service = ChatService(session)
            first = await service.process_message(
                family_id=family_id, member_id=member_id, conversation_id=None,
                message="When is the electricity bill due?",
            )
            second = await service.process_message(
                family_id=family_id, member_id=member_id, conversation_id=first.conversation_id,
                message="Is it still pending?",
            )

            assert first.assistant_message == "The electricity bill is due October 18."
            assert second.assistant_message == "The electricity bill is still pending."
            second_prompt = model.calls[1]["messages"]
            assert {"role": "user", "content": "When is the electricity bill due?"} in second_prompt
            assert {"role": "assistant", "content": "The electricity bill is due October 18."} in second_prompt
            assert "The person speaking is Rahul" in second_prompt[0]["content"]
            assert "Electricity Bill" in second_prompt[0]["content"]
            assert "Internet Bill" in second_prompt[0]["content"]
            assert "Secret Other Bill" not in second_prompt[0]["content"]
            assert "Other Family" not in second_prompt[0]["content"]
            # The current context contract intentionally contains members, active
            # commitments and dependencies; expense inclusion is not documented.
            assert len(model.calls[0]["messages"]) > 0

            conversation = await session.get(Conversation, first.conversation_id)
            messages = list((await session.scalars(
                select(Message).where(Message.conversation_id == first.conversation_id).order_by(Message.created_at, Message.id)
            )).all())
            assert conversation.family_id == family_id
            assert sorted((m.role, m.content) for m in messages) == sorted([
                ("user", "When is the electricity bill due?"),
                ("assistant", "The electricity bill is due October 18."),
                ("user", "Is it still pending?"),
                ("assistant", "The electricity bill is still pending."),
            ])
            assert await service.get_history(family_id=family_id, conversation_id=first.conversation_id)
            events = list((await session.scalars(
                select(AgentEvent).where(AgentEvent.family_id == family_id)
            )).all())
            assert len(events) == 2
            assert all(event.event_data["member_id"] == str(member_id) for event in events)
        finally:
            await _cleanup(session, [family_id, other_family_id])


@pytest.mark.asyncio(loop_scope="session")
async def test_chat_search_then_update_changes_same_unambiguous_commitment(monkeypatch):
    import app.services.chat as chat_module

    family_id, member_id, sibling_id = uuid4(), uuid4(), uuid4()
    bill = _bill(family_id, member_id, "Electricity Bill", date(2026, 10, 18))
    sibling_bill = _bill(family_id, sibling_id, "Electricity Bill", date(2026, 10, 18))
    model = ScriptedChatModel([
        _tool("search_commitments", {"title_query": "electricity bill", "member_id": str(member_id), "status": "PENDING"}, "search"),
        _tool("update_commitment", {"commitment_id": str(bill.id), "status": "COMPLETED"}, "update"),
        AIResponse(content="Marked the electricity bill as paid.", tool_calls=[]),
    ])
    monkeypatch.setattr(chat_module, "AIModelClient", lambda: model)

    async with AsyncSessionLocal() as session:
        session.add_all([
            Family(id=family_id, name="Update Family"),
            FamilyMember(id=member_id, family_id=family_id, name="Rahul", relationship_type="PARENT"),
            FamilyMember(id=sibling_id, family_id=family_id, name="Maya", relationship_type="CHILD"),
            bill, sibling_bill,
        ])
        await session.flush()
        try:
            result = await ChatService(session).process_message(
                family_id=family_id, member_id=member_id, conversation_id=None,
                message="I paid the electricity bill.",
            )
            await session.refresh(bill)
            await session.refresh(sibling_bill)
            rows = list((await session.scalars(select(Commitment).where(Commitment.family_id == family_id))).all())
            assert [call["name"] for call in result.tool_calls] == ["search_commitments", "update_commitment"]
            assert result.tool_results[1]["result"]["success"] is True
            assert bill.status == CommitmentStatus.COMPLETED.value
            assert len(rows) == 2
            assert bill.status == CommitmentStatus.COMPLETED.value
            assert sibling_bill.status == CommitmentStatus.PENDING.value
        finally:
            await _cleanup(session, [family_id])


@pytest.mark.asyncio(loop_scope="session")
async def test_chat_update_tool_asks_for_clarification_after_multiple_matches(monkeypatch):
    """Reproduce whether a tool caller can bypass the documented clarify-first rule."""
    import app.services.chat as chat_module

    family_id, member_id = uuid4(), uuid4()
    october = _bill(family_id, member_id, "Electricity Bill", date(2026, 10, 18))
    november = _bill(family_id, member_id, "Electricity Bill", date(2026, 11, 18))
    # This deliberately scripts a model that ignores the search result's warning.
    model = ScriptedChatModel([
        _tool("search_commitments", {"title_query": "electricity bill", "status": "PENDING"}, "search"),
        _tool("update_commitment", {"commitment_id": str(october.id), "status": "COMPLETED"}, "unsafe-update"),
        AIResponse(content="Marked it paid.", tool_calls=[]),
    ])
    monkeypatch.setattr(chat_module, "AIModelClient", lambda: model)

    async with AsyncSessionLocal() as session:
        session.add_all([
            Family(id=family_id, name="Ambiguity Family"),
            FamilyMember(id=member_id, family_id=family_id, name="Rahul", relationship_type="PARENT"),
            october, november,
        ])
        await session.flush()
        try:
            result = await ChatService(session).process_message(
                family_id=family_id, member_id=member_id, conversation_id=None,
                message="I paid the electricity bill.",
            )
            await session.refresh(october)
            await session.refresh(november)
            assert result.tool_results[0]["result"]["count"] == 2
            assert result.requires_clarification is True
            assert "multiple matching commitments" in result.assistant_message.casefold()

            assert october.status == CommitmentStatus.PENDING.value
            assert november.status == CommitmentStatus.PENDING.value

            assert [call["name"] for call in result.tool_calls] == [
                "search_commitments"
            ]
        finally:
            await _cleanup(session, [family_id])


@pytest.mark.asyncio(loop_scope="session")
async def test_chat_accepts_unknown_member_id_without_rejecting_request(monkeypatch):
    import app.services.chat as chat_module

    family_id, real_member_id, unknown_member_id = uuid4(), uuid4(), uuid4()
    model = ScriptedChatModel([AIResponse(content="Hello.", tool_calls=[])])
    monkeypatch.setattr(chat_module, "AIModelClient", lambda: model)
    async with AsyncSessionLocal() as session:
        session.add_all([
            Family(id=family_id, name="Member Contract Family"),
            FamilyMember(id=real_member_id, family_id=family_id, name="Rahul", relationship_type="PARENT"),
        ])
        await session.flush()
        try:
            result = await ChatService(session).process_message(
                family_id=family_id, member_id=unknown_member_id, conversation_id=None,
                message="Hello",
            )
            assert result.assistant_message == "Hello."
            assert "The person speaking is" not in model.calls[0]["messages"][0]["content"]
        finally:
            await _cleanup(session, [family_id])
