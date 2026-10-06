import json
from typing import Any

from app.agents.prompts import SYSTEM_PROMPT
from app.agents.state import AgentState
from app.clients.ai_model import AIModelClient
from app.core.config import get_settings
from app.tools.registry import ToolRegistry
from app.utils.dates import resolve_expense_date


_CONFIRMATION_REPLIES = {
    "yes",
    "yes please",
    "yeah",
    "yep",
    "correct",
    "that's right",
    "that is right",
    "right",
    "sure",
    "ok",
    "okay",
}


def _expense_date_source(state: AgentState) -> str:
    """Preserve date intent through a pending expense clarification exchange."""

    history = list(state.history)
    if (
        history
        and history[-1].get("role") == "user"
        and history[-1].get("content", "").strip() == state.user_message.strip()
    ):
        history.pop()

    last_assistant = next(
        (item for item in reversed(history) if item.get("role") == "assistant"),
        None,
    )
    if last_assistant is None:
        return state.user_message

    question = last_assistant.get("content", "")
    normalized_question = question.casefold()
    clarification_terms = (
        "expense",
        "spend",
        "amount",
        "date",
        "category",
        "merchant",
        "did you mean",
        "which one",
    )
    if "?" not in question or not any(term in normalized_question for term in clarification_terms):
        return state.user_message

    user_messages = [state.user_message]
    for item in reversed(history):
        role = item.get("role")
        if role == "assistant":
            if "?" not in item.get("content", ""):
                break
        elif role == "user":
            content = item.get("content", "")
            if content.strip().casefold().rstrip(".! ") not in _CONFIRMATION_REPLIES:
                user_messages.append(content)

    return "\n".join(reversed(user_messages))


class FamilyContextAgent:
    def __init__(
        self,
        ai_client: AIModelClient,
        tool_registry: ToolRegistry,
    ) -> None:
        self.ai_client = ai_client
        self.tool_registry = tool_registry

    async def run(self, state: AgentState) -> AgentState:
        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
        ]

        for history_message in state.history:
            messages.append(
                {
                    "role": history_message["role"],
                    "content": history_message["content"],
                }
            )

        tool_definitions = self.tool_registry.definitions()
        max_tool_rounds = 5

        for _ in range(max_tool_rounds):
            response = await self.ai_client.chat(
                messages=messages,
                tools=tool_definitions,
            )

            # No tool requested by the AI.
            # Return the normal assistant response.
            if not response.tool_calls:
                state.assistant_message = (
                    response.content
                    or "I couldn't generate a response."
                )
                return state

            # Add the assistant's tool request to the conversation.
            assistant_message = {
                "role": "assistant",
                "content": response.content,
                "tool_calls": [],
            }

            for tool_call in response.tool_calls:
                assistant_message["tool_calls"].append(
                    {
                        "id": tool_call.call_id,
                        "type": "function",
                        "function": {
                            "name": tool_call.name,
                            "arguments": json.dumps(
                                tool_call.arguments
                            ),
                        },
                    }
                )

            messages.append(assistant_message)

            # Execute every tool requested by the AI.
            for tool_call in response.tool_calls:
                arguments = dict(tool_call.arguments)

                # family_id is application context.
                # The user does not need to provide it.
                arguments["family_id"] = str(state.family_id)

                try:
                    if tool_call.name == "add_expense":
                        resolved_date = resolve_expense_date(
                            _expense_date_source(state),
                            get_settings().family_timezone,
                        )
                        # Tool arguments are model-proposed; the original user
                        # message and application timezone determine the date.
                        arguments["expense_date"] = resolved_date.isoformat()

                    result = await self.tool_registry.dispatch(
                        tool_call.name,
                        arguments,
                    )
                except Exception as exc:
                    result = {
                        "success": False,
                        "error": str(exc),
                    }

                state.tool_calls.append(
                    {
                        "name": tool_call.name,
                        "arguments": arguments,
                    }
                )

                state.tool_results.append(
                    {
                        "tool": tool_call.name,
                        "result": result,
                    }
                )

                # Send the tool result back to the AI so it can
                # generate the final natural-language response.
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.call_id,
                        "content": json.dumps(
                            result,
                            default=str,
                        ),
                    }
                )

        # Safety fallback if the AI keeps requesting tools.
        state.assistant_message = (
            "I couldn't complete the request safely. "
            "Please try again."
        )
        return state
FamilyContextOrchestrator = FamilyContextAgent
