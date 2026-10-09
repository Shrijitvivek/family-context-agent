from uuid import uuid4

import httpx
import pytest

from app.agents.state import AgentState
from app.api.dependencies import get_db
from app.api.v1.endpoints import chat as chat_endpoint
from app.main import app


class FakeChatService:
    received: dict | None = None

    def __init__(self, _session) -> None:
        pass

    async def process_message(self, **kwargs) -> AgentState:
        type(self).received = kwargs
        state = AgentState(
            family_id=kwargs["family_id"],
            user_id=kwargs["user_id"],
            conversation_id=kwargs["conversation_id"] or uuid4(),
            user_message=kwargs["message"],
        )
        state.assistant_message = "Transport expense recorded."
        state.tool_calls.append({"name": "add_expense", "arguments": {"amount": 120}})
        state.tool_results.append({"tool": "add_expense", "result": {"success": True}})
        return state


@pytest.mark.asyncio
async def test_chat_api_routes_to_current_chat_service_interface(monkeypatch) -> None:
    async def fake_db():
        yield object()

    previous_overrides = dict(app.dependency_overrides)
    app.dependency_overrides[get_db] = fake_db
    monkeypatch.setattr(chat_endpoint, "ChatService", FakeChatService)
    family_id = uuid4()
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/chat",
                json={"family_id": str(family_id), "message": "I spent 120 on transport"},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["message"] == "Transport expense recorded."
        assert body["tool_calls"][0]["name"] == "add_expense"
        assert body["tool_results"][0]["result"]["success"] is True
        assert FakeChatService.received == {
            "family_id": family_id,
            "user_id": None,
            "conversation_id": None,
            "message": "I spent 120 on transport",
            "document_id": None,
        }
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)
