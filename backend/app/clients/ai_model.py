
"""AI model client for the Family Context Agent."""

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
        self.base_url = settings.nebius_base_url.rstrip("/")
        self.model = settings.nvidia_model_name
        self.vision_model = settings.vision_model_name
        self.timeout_seconds = settings.model_timeout_seconds

        if not self.api_key:
            raise ValueError("NEBIUS_API_KEY is not configured.")

        if not self.base_url:
            raise ValueError("NEBIUS_BASE_URL is not configured.")

        if not self.model:
            raise ValueError("NVIDIA_MODEL_NAME is not configured.")

        if self.timeout_seconds <= 0:
            raise ValueError("MODEL_TIMEOUT_SECONDS must be positive.")

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _timeout(self) -> float:
        # The fallback preserves compatibility with tests that construct
        # the client using __new__ instead of calling __init__.
        return getattr(self, "timeout_seconds", 60.0)

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1000,
    ) -> AIResponse:
        """Send a chat request and validate the returned message."""

        url = f"{self.base_url.rstrip('/')}/chat/completions"

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        try:
            async with httpx.AsyncClient(
                timeout=self._timeout()
            ) as client:
                response = await client.post(
                    url,
                    headers=self._headers(),
                    json=payload,
                )
                response.raise_for_status()

            data = response.json()

            if not isinstance(data, dict):
                raise AIModelError(
                    "Nebius returned an invalid response object."
                )

            choices = data.get("choices")
            if not isinstance(choices, list) or not choices:
                raise AIModelError(
                    "Nebius response did not contain any choices."
                )

            message = choices[0].get("message")
            if not isinstance(message, dict):
                raise AIModelError(
                    "Nebius response did not contain a valid message."
                )

            content = message.get("content")
            if content is not None and not isinstance(content, str):
                raise AIModelError(
                    "Nebius returned invalid message content."
                )

            raw_tool_calls = message.get("tool_calls") or []
            if not isinstance(raw_tool_calls, list):
                raise AIModelError(
                    "Nebius returned invalid tool calls."
                )

            tool_calls: list[ToolCallRequest] = []

            for item in raw_tool_calls:
                if not isinstance(item, dict):
                    raise AIModelError(
                        "Nebius returned an invalid tool call."
                    )

                function = item.get("function")
                if not isinstance(function, dict):
                    raise AIModelError(
                        "Nebius tool call has no valid function."
                    )

                name = function.get("name")
                call_id = item.get("id")
                raw_arguments = function.get("arguments", "{}")

                if not isinstance(name, str) or not name.strip():
                    raise AIModelError(
                        "Nebius tool call has no valid function name."
                    )

                if not isinstance(call_id, str) or not call_id.strip():
                    raise AIModelError(
                        "Nebius tool call has no valid call ID."
                    )

                if isinstance(raw_arguments, str):
                    try:
                        arguments = json.loads(raw_arguments)
                    except json.JSONDecodeError as exc:
                        raise AIModelError(
                            "Nebius returned malformed tool arguments."
                        ) from exc
                else:
                    arguments = raw_arguments

                if not isinstance(arguments, dict):
                    raise AIModelError(
                        "Nebius tool arguments must be a JSON object."
                    )

                tool_calls.append(
                    ToolCallRequest(
                        name=name,
                        arguments=arguments,
                        call_id=call_id,
                    )
                )

            return AIResponse(
                content=content,
                tool_calls=tool_calls,
            )

        except AIModelError:
            raise
        except httpx.TimeoutException as exc:
            raise AIModelError(
                "Nebius API request timed out."
            ) from exc
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code

            if status in (401, 403):
                message = (
                    "Nebius API authentication failed. "
                    "Check NEBIUS_API_KEY and its permissions."
                )
            elif status == 429:
                message = (
                    "Nebius API rate limit or quota was exceeded."
                )
            else:
                message = f"Nebius API returned HTTP {status}."

            raise AIModelError(message) from exc
        except httpx.HTTPError as exc:
            raise AIModelError(
                "Could not connect to the Nebius API."
            ) from exc
        except (ValueError, TypeError, KeyError, IndexError) as exc:
            raise AIModelError(
                "Nebius returned an invalid response."
            ) from exc

    async def complete_json(
        self,
        messages: list[dict[str, Any]],
        *,
        model: str | None = None,
    ) -> dict[str, Any]:
        """Request and validate a JSON-object response from the model."""

        url = f"{self.base_url.rstrip('/')}/chat/completions"

        payload: dict[str, Any] = {
            "model": model or self.model,
            "messages": messages,
            "temperature": 0.0,
            "max_tokens": 8192, 
            "response_format": {"type": "json_object"},
        }

        try:
            async with httpx.AsyncClient(
                timeout=self._timeout()
            ) as client:
                response = await client.post(
                    url,
                    headers=self._headers(),
                    json=payload,
                )
                response.raise_for_status()

            data = response.json()

            if not isinstance(data, dict):
                raise AIModelError(
                    "Nebius returned an invalid response object."
                )

            choices = data.get("choices")
            if not isinstance(choices, list) or not choices:
                raise AIModelError(
                    "Nebius response did not contain any choices."
                )

            message = choices[0].get("message")
            if not isinstance(message, dict):
                raise AIModelError(
                    "Nebius response did not contain a valid message."
                )

            content = message.get("content")
            if not isinstance(content, str) or not content.strip():
                raise AIModelError(
                    "Model returned empty content."
                )

            result = json.loads(content)

            if not isinstance(result, dict):
                raise AIModelError(
                    "Model returned invalid JSON object."
                )

            return result

        except AIModelError:
            raise
        except httpx.TimeoutException as exc:
            raise AIModelError(
                "Nebius API request timed out."
            ) from exc
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code

            if status in (401, 403):
                message = (
                    "Nebius API authentication failed. "
                    "Check NEBIUS_API_KEY and its permissions."
                )
            elif status == 429:
                message = (
                    "Nebius API rate limit or quota was exceeded."
                )
            else:
                message = f"Nebius API returned HTTP {status}."

            raise AIModelError(message) from exc
        except httpx.HTTPError as exc:
            raise AIModelError(
                "Could not connect to the Nebius API."
            ) from exc
        except (ValueError, TypeError, KeyError, IndexError) as exc:
            raise AIModelError(
                "Nebius returned invalid JSON or response data."
            ) from exc
