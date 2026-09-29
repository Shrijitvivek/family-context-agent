"""
AI model client for the Family Context Agent.

Responsibilities:
- Call the NVIDIA/Nebius OpenAI-compatible API.
- Send tool definitions to the model.
- Read normal assistant responses.
- Read structured tool calls.
- Keep all model communication in one place.
"""

import json
import os
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class ToolCallRequest:
    """A tool requested by the AI model."""

    name: str
    arguments: dict[str, Any]
    call_id: str


@dataclass
class AIResponse:
    """Normalized response returned by the model client."""

    content: str | None
    tool_calls: list[ToolCallRequest]


class AIModelClient:

    def __init__(self) -> None:
        self.api_key = os.getenv("NVIDIA_API_KEY")

        self.base_url = os.getenv(
            "NVIDIA_API_URL",
            "https://integrate.api.nvidia.com/v1",
        )

        self.model = os.getenv(
            "NVIDIA_MODEL",
            "meta/llama-3.1-8b-instruct",
        )

        if not self.api_key:
            raise ValueError(
                "NVIDIA_API_KEY is not configured."
            )

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1000,
    ) -> AIResponse:

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

        for tool_call in message.get("tool_calls", []):

            function = tool_call.get("function", {})

            arguments_raw = function.get(
                "arguments",
                "{}",
            )

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
"""Nebius-hosted NVIDIA model client (OpenAI-compatible chat completions).

Services depend on the ``ModelClient`` protocol, so tests can pass a fake.
Prompts, responses, and document content are never logged.
"""

import json
import logging
from typing import Any, Protocol

import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from app.agents.orchestrator import decision_from_model_tool_call
from app.core.config import Settings, get_settings
from app.core.exceptions import AIModelError
from app.schemas.agent import AgentDecision

logger = logging.getLogger(__name__)


class ModelClient(Protocol):
    async def decide(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> AgentDecision: ...

    async def complete_json(self, messages: list[dict[str, Any]]) -> dict[str, Any]: ...


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, httpx.TransportError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code == 429 or exc.response.status_code >= 500
    return False


def _parse_json_object(text: str) -> dict[str, Any]:
    """Parse a JSON object, tolerating Markdown code fences around it."""

    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise AIModelError("The model did not return a JSON object.")
    try:
        value = json.loads(text[start : end + 1])
    except ValueError as exc:
        raise AIModelError("The model returned malformed JSON.") from exc
    if not isinstance(value, dict):
        raise AIModelError("The model did not return a JSON object.")
    return value


class AIModelClient:
    def __init__(
        self,
        settings: Settings | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._http = http_client

    @property
    def configured(self) -> bool:
        return bool(self._settings.nebius_api_key and self._settings.nvidia_model_name)

    async def _chat(self, body: dict[str, Any]) -> dict[str, Any]:
        if not self.configured:
            raise AIModelError("The AI model is not configured (NEBIUS_API_KEY/NVIDIA_MODEL_NAME).")

        body = {"model": self._settings.nvidia_model_name, "temperature": 0, **body}
        headers = {"Authorization": f"Bearer {self._settings.nebius_api_key}"}
        url = self._settings.nebius_base_url.rstrip("/") + "/chat/completions"
        client = self._http or httpx.AsyncClient(timeout=self._settings.model_timeout_seconds)
        try:
            async for attempt in AsyncRetrying(
                retry=retry_if_exception(_is_retryable),
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=0.5, max=4),
                reraise=True,
            ):
                with attempt:
                    response = await client.post(url, json=body, headers=headers)
                    response.raise_for_status()
                    return response.json()
        except httpx.HTTPStatusError as exc:
            logger.warning("model_request_failed", extra={"status": exc.response.status_code})
            raise AIModelError("The AI model request failed.") from exc
        except httpx.HTTPError as exc:
            logger.warning("model_request_failed", extra={"error": type(exc).__name__})
            raise AIModelError("The AI model could not be reached.") from exc
        finally:
            if self._http is None:
                await client.aclose()
        raise AIModelError("The AI model request failed.")  # pragma: no cover

    @staticmethod
    def _first_message(payload: dict[str, Any]) -> dict[str, Any]:
        try:
            return payload["choices"][0]["message"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AIModelError("The AI model returned an unexpected response.") from exc

    async def decide(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> AgentDecision:
        """Ask the model to either call one tool or reply in plain text."""

        payload = await self._chat({"messages": messages, "tools": tools, "tool_choice": "auto"})
        message = self._first_message(payload)
        tool_calls = message.get("tool_calls") or []
        if tool_calls:
            function = tool_calls[0].get("function") or {}
            return decision_from_model_tool_call(
                function.get("name", ""), function.get("arguments")
            )
        content = (message.get("content") or "").strip()
        if not content:
            return AgentDecision.ask("Sorry, I didn't catch that. Could you say it again?")
        return AgentDecision.answer(content)

    async def complete_json(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        """Ask for one JSON object (used for document field extraction)."""

        payload = await self._chat({"messages": messages})
        return _parse_json_object(self._first_message(payload).get("content") or "")
