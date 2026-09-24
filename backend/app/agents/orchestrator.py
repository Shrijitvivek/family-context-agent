"""
Family Context Agent orchestration.

Flow:

User
 ↓
AI
 ↓
Tool selection
 ↓
Tool Registry
 ↓
Service
 ↓
PostgreSQL
 ↓
Tool result
 ↓
AI
 ↓
Final response
"""

import json
from typing import Any

from app.agents.prompts import (
    SYSTEM_PROMPT,
    build_user_prompt,
)
from app.agents.state import AgentState
from app.clients.ai_model import AIModelClient
from app.tools.registry import ToolRegistry


class FamilyContextAgent:

    def __init__(
        self,
        ai_client: AIModelClient,
        tool_registry: ToolRegistry,
    ) -> None:

        self.ai_client = ai_client
        self.tool_registry = tool_registry

    async def run(
        self,
        state: AgentState,
    ) -> AgentState:

        messages: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": build_user_prompt(
                    state.user_message
                ),
            },
        ]

        # Give the AI access to the seven registered tools.
        tool_definitions = (
            self.tool_registry.definitions()
        )

        # Limit loops so a faulty model cannot call
        # tools forever.
        max_tool_rounds = 5

        for _ in range(max_tool_rounds):

            response = await self.ai_client.chat(
                messages=messages,
                tools=tool_definitions,
            )

            # -----------------------------------------
            # CASE 1:
            # AI has finished and wants to answer user.
            # -----------------------------------------

            if not response.tool_calls:

                state.assistant_message = (
                    response.content
                    or "I couldn't generate a response."
                )

                return state

            # -----------------------------------------
            # CASE 2:
            # AI wants to call one or more tools.
            # -----------------------------------------

            assistant_message: dict[str, Any] = {
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

            # Execute each requested tool.
            for tool_call in response.tool_calls:

                arguments = dict(
                    tool_call.arguments
                )

                # The family ID is controlled by the API request,
                # not invented by the model.
                arguments["family_id"] = (
                    str(state.family_id)
                )

                # Store observable tool activity.
                state.tool_calls.append(
                    {
                        "name": tool_call.name,
                        "arguments": arguments,
                    }
                )

                try:

                    result = (
                        await self.tool_registry.dispatch(
                            tool_call.name,
                            arguments,
                        )
                    )

                except Exception as exc:

                    # Return the error to the model so it can
                    # explain the failure instead of claiming success.
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

                # Send the tool result back to the AI.
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": (
                            tool_call.call_id
                        ),
                        "content": json.dumps(
                            result,
                            default=str,
                        ),
                    }
                )

        # Maximum tool rounds reached.
        state.assistant_message = (
            "I couldn't complete the request safely. "
            "Please try again."
        )

        return state