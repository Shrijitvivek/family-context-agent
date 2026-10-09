import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.clients.ai_model import AIModelClient


@pytest.mark.asyncio
async def test_ai_model_client_normal_response():
    client = AIModelClient.__new__(AIModelClient)

    client.api_key = "test-key"
    client.base_url = "https://example.com/v1"
    client.model = "test-model"

    mock_response = {
        "choices": [
            {
                "message": {
                    "content": "Your expense was recorded.",
                }
            }
        ]
    }

    request = httpx.Request(
        "POST",
        "https://example.com/v1/chat/completions",
    )

    response = httpx.Response(
        200,
        json=mock_response,
        request=request,
    )

    with patch(
        "app.clients.ai_model.httpx.AsyncClient"
    ) as mock_client:

        mock_http = AsyncMock()
        mock_http.post.return_value = response

        mock_client.return_value.__aenter__.return_value = (
            mock_http
        )

        result = await client.chat(
            messages=[
                {
                    "role": "user",
                    "content": "Record my expense.",
                }
            ]
        )

    assert result.content == "Your expense was recorded."

    assert result.tool_calls == []


@pytest.mark.asyncio
async def test_ai_model_client_tool_call_response():
    client = AIModelClient.__new__(AIModelClient)

    client.api_key = "test-key"
    client.base_url = "https://example.com/v1"
    client.model = "test-model"

    mock_response = {
        "choices": [
            {
                "message": {
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_123",
                            "type": "function",
                            "function": {
                                "name": "add_expense",
                                "arguments": json.dumps(
                                    {
                                        "amount": "850.00",
                                        "category": "GROCERIES",
                                        "expense_date": "2026-09-27",
                                    }
                                ),
                            },
                        }
                    ],
                }
            }
        ]
    }

    request = httpx.Request(
        "POST",
        "https://example.com/v1/chat/completions",
    )

    response = httpx.Response(
        200,
        json=mock_response,
        request=request,
    )

    with patch(
        "app.clients.ai_model.httpx.AsyncClient"
    ) as mock_client:

        mock_http = AsyncMock()
        mock_http.post.return_value = response

        mock_client.return_value.__aenter__.return_value = (
            mock_http
        )

        result = await client.chat(
            messages=[
                {
                    "role": "user",
                    "content": "I spent ₹850 on groceries.",
                }
            ],
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "add_expense",
                    },
                }
            ],
        )

    assert result.content is None

    assert len(result.tool_calls) == 1

    tool_call = result.tool_calls[0]

    assert tool_call.name == "add_expense"

    assert tool_call.call_id == "call_123"

    assert tool_call.arguments == {
        "amount": "850.00",
        "category": "GROCERIES",
        "expense_date": "2026-09-27",
    }