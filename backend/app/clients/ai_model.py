"""
AI model client for the Family Context Agent.

Responsibilities:
- Call the Nebius Token Factory OpenAI-compatible API.
- Send tool definitions to the model.
- Read normal assistant responses.
- Read structured tool calls.
- Keep all model communication in one place.
"""

import json
from app.core.config import Settings
from dataclasses import dataclass
from typing import Any

import httpx


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

        # Some OpenAI-compatible providers return
        # "tool_calls": None when there are no tool calls.
        # Using "or []" safely handles both None and [].
        for tool_call in message.get("tool_calls") or []:
            function = tool_call.get("function", {})

            arguments_raw = function.get("arguments", "{}")

            try:
                arguments = json.loads(arguments_raw)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"AI returned invalid tool arguments "
                    f"for {function.get('name')}"
                ) from exc

            tool_calls.append(
                ToolCallRequest(
                    name=function["name"],
                    arguments=arguments,
                    call_id=tool_call.get(
                        "id",
                        function["name"],
                    ),
                )
            )

        return AIResponse(
            content=content,
            tool_calls=tool_calls,
        )
