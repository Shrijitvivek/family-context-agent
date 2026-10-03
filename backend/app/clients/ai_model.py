"""
AI model client for the Family Context Agent.

Responsibilities:
- Call the Nebius Token Factory OpenAI-compatible API.
- Send tool definitions to the model.
- Read normal assistant responses.
- Read structured tool calls.
- Request structured JSON responses for document extraction.
- Keep all model communication in one place.
"""

import json
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import Settings
from app.core.exceptions import AIModelError


@dataclass
class ToolCallRequest:
    name: str
    arguments: dict[str, Any]
    call_id: str


@dataclass
class AIResponse:
    content: str | None
    tool_calls: list[ToolCallRequest]


class AIModelClient:
    def __init__(self) -> None:
        settings = Settings()

        self.api_key = settings.nebius_api_key
        self.base_url = settings.nebius_base_url
        self.model = settings.nvidia_model_name

        if not self.api_key:
            raise ValueError("NEBIUS_API_KEY is not configured.")

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1000,
    ) -> AIResponse:
        """
        Send a chat request to the Nebius Token Factory API.

        Returns:
            AIResponse containing the assistant's text response
            and any requested tool calls.
        """

        url = f"{self.base_url.rstrip('/')}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                headers=headers,
                json=payload,
            )

            response.raise_for_status()

        data = response.json()

        message = data["choices"][0]["message"]

        content = message.get("content")

        tool_calls: list[ToolCallRequest] = []

        for tool_call in message.get("tool_calls") or []:
            function = tool_call["function"]

            arguments = function.get("arguments", "{}")

            if isinstance(arguments, str):
                arguments = json.loads(arguments)

            tool_calls.append(
                ToolCallRequest(
                    name=function["name"],
                    arguments=arguments,
                    call_id=tool_call["id"],
                )
            )

        return AIResponse(
            content=content,
            tool_calls=tool_calls,
        )

    async def complete_json(
        self,
        messages: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Request a structured JSON response from the model."""

        url = f"{self.base_url.rstrip('/')}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.0,
            "max_tokens": 1000,
            "response_format": {
                "type": "json_object",
            },
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    url,
                    headers=headers,
                    json=payload,
                )

                response.raise_for_status()

            data = response.json()
            content = data["choices"][0]["message"].get("content")

            if not content:
                raise AIModelError("Model returned empty content.")

            result = json.loads(content)

            if not isinstance(result, dict):
                raise AIModelError("Model returned invalid JSON.")

            return result

        except AIModelError:
            raise
        except (
            httpx.HTTPError,
            KeyError,
            TypeError,
            json.JSONDecodeError,
        ) as exc:
            raise AIModelError(str(exc)) from exc