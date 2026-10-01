import json
import re
from datetime import date, datetime, timedelta
from typing import Any

from app.agents.prompts import SYSTEM_PROMPT
from app.agents.state import AgentState
from app.clients.ai_model import AIModelClient
from app.core.config import get_settings
from app.tools.registry import ToolRegistry
from app.utils.dates import today_in


_ISO_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
_INDIAN_DATE = re.compile(r"\b\d{1,2}/\d{1,2}/\d{4}\b")


def _expense_date_from_request(message: str, today: date) -> date:
    """Resolve explicit and relative dates from the user's own words."""
    for pattern, date_format in ((_ISO_DATE, "%Y-%m-%d"), (_INDIAN_DATE, "%d/%m/%Y")):
        for match in pattern.finditer(message):
            try:
                return datetime.strptime(match.group(), date_format).date()
            except ValueError:
                continue

    request = message.casefold()
    if re.search(r"\byesterday\b", request):
        return today - timedelta(days=1)
    if re.search(r"\btomorrow\b", request):
        return today + timedelta(days=1)
    return today


class FamilyContextAgent:
    def __init__(
        self,
        ai_client: AIModelClient,
        tool_registry: ToolRegistry,
    ) -> None:
        self.ai_client = ai_client
        self.tool_registry = tool_registry

    async def run(self, state: AgentState) -> AgentState:
        timezone = get_settings().family_timezone
        today = today_in(timezone)
        messages = [
            {
                "role": "system",
                "content": f"{SYSTEM_PROMPT}\n\nCurrent date in the family timezone "
                f"({timezone}): {today.isoformat()}.",
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

                # Resolve from the user's request, never a model guess.
                if tool_call.name == "add_expense":
                    arguments["expense_date"] = _expense_date_from_request(
                        state.user_message, today
                    ).isoformat()

                state.tool_calls.append(
                    {
                        "name": tool_call.name,
                        "arguments": arguments,
                    }
                )

                try:
                    result = await self.tool_registry.dispatch(
                        tool_call.name,
                        arguments,
                    )
                except Exception as exc:
                    result = {
                        "success": False,
                        "error": str(exc),
                    }

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