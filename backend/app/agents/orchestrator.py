
"""Orchestrate AI responses and family-context tool execution."""

import json

from app.agents.clarification import build_clarification
from app.agents.prompts import SYSTEM_PROMPT
from app.agents.state import AgentState
from app.clients.ai_model import AIModelClient
from app.core.config import get_settings
from app.tools.registry import ToolRegistry
from app.utils.dates import (
    contains_relative_expense_date,
    resolve_commitment_due_date,
    resolve_expense_date,
    today_in,
)


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

_DATE_REQUIRED_COMMITMENT_TYPES = {
    "BILL",
    "APPOINTMENT",
    "LAB_TEST",
    "DEADLINE",
    "RENEWAL",
}


def _expense_date_source(state: AgentState) -> str:
    """Preserve date intent through an expense clarification exchange."""
    history = list(state.history)

    if (
        history
        and history[-1].get("role") == "user"
        and history[-1].get("content", "").strip()
        == state.user_message.strip()
    ):
        history.pop()

    last_assistant = next(
        (
            item
            for item in reversed(history)
            if item.get("role") == "assistant"
        ),
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

    if "?" not in question or not any(
        term in normalized_question for term in clarification_terms
    ):
        return state.user_message

    user_messages = [state.user_message]

    for item in reversed(history):
        role = item.get("role")

        if role == "assistant":
            if "?" not in item.get("content", ""):
                break

        elif role == "user":
            content = item.get("content", "")

            if (
                content.strip().casefold().rstrip(".! ")
                not in _CONFIRMATION_REPLIES
            ):
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
        current_date = today_in(get_settings().family_timezone).isoformat()
        context_section = (
            "\n\nAPPLICATION DATE CONTEXT\n"
            f"Today is {current_date} in the family's configured timezone. "
            "Yesterday and last day mean one calendar day before today."
        )

        if state.household_context:
            context_section += f"""

CURRENT HOUSEHOLD CONTEXT
=========================

The following information comes from the application's
database and represents the current household state.

{state.household_context}

Use this information when answering questions about
the family.

Do not invent household information that is not present
in this context or available through tools.

If the context is insufficient, use the appropriate tool
or ask the user for clarification.
"""

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT + context_section,
            },
        ]

        for history_message in state.history:
            messages.append(
                {
                    "role": history_message["role"],
                    "content": history_message["content"],
                }
            )

        document = state.metadata.get("document")

        if document:
            document_context = (
                "The user attached the following document. "
                "Use this document as the primary source when answering "
                "questions about it.\n\n"
                f"File name: {document.get('file_name')}\n"
                f"Document type: {document.get('document_type')}\n"
                f"Processing status: "
                f"{document.get('processing_status')}\n"
                f"Extracted text: "
                f"{document.get('extracted_text')}\n"
                f"Extracted data: "
                f"{json.dumps(document.get('extracted_data'), default=str)}"
            )

            messages.append(
                {
                    "role": "system",
                    "content": document_context,
                }
            )

        tool_definitions = self.tool_registry.definitions()
        max_tool_rounds = 5

        for _ in range(max_tool_rounds):
            response = await self.ai_client.chat(
                messages=messages,
                tools=tool_definitions,
            )

            if not response.tool_calls:
                state.assistant_message = (
                    response.content
                    or "I couldn't generate a response."
                )
                return state

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

            for tool_call in response.tool_calls:
                arguments = dict(tool_call.arguments)

                # Add application-owned family context.
                arguments["family_id"] = str(state.family_id)

                if tool_call.name in {
                    "add_expense",
                    "create_commitment",
                }:
                    if state.member_id is not None:
                        arguments["member_id"] = str(state.member_id)

                # Resolve dates before checking missing fields.
                if tool_call.name == "add_expense":
                    try:
                        resolved_date = resolve_expense_date(
                            _expense_date_source(state),
                            get_settings().family_timezone,
                        )
                    except ValueError as exc:
                        state.assistant_message = str(exc)
                        return state
                    arguments["expense_date"] = (
                        resolved_date.isoformat()
                    )

                elif tool_call.name == "get_expense_records":
                    if state.member_id is not None:
                        arguments["member_id"] = str(state.member_id)

                    if contains_relative_expense_date(state.user_message):
                        resolved_date = resolve_expense_date(
                            state.user_message,
                            get_settings().family_timezone,
                        )
                        arguments["start_date"] = resolved_date.isoformat()
                        arguments["end_date"] = resolved_date.isoformat()

                elif tool_call.name == "create_commitment":
                    commitment_type = str(
                        arguments.get("commitment_type", "")
                    ).upper()

                    if commitment_type in _DATE_REQUIRED_COMMITMENT_TYPES:
                        try:
                            resolved_due_date = (
                                resolve_commitment_due_date(
                                    state.user_message,
                                    get_settings().family_timezone,
                                )
                            )
                        except ValueError:
                            # A missing or unsupported date must not
                            # silently default to today. Allow the
                            # clarification layer to ask for a date.
                            arguments.pop("due_date", None)
                        else:
                            arguments["due_date"] = (
                                resolved_due_date.isoformat()
                            )

                    clarification = build_clarification(
                        tool_call.name,
                        arguments,
                    )

                    if (
                        clarification is not None
                        and clarification.clarification is not None
                    ):
                        state.assistant_message = (
                            clarification.clarification.question
                        )
                        return state

                # Execute the tool after validation.
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

        state.assistant_message = (
            "I couldn't complete the request safely. "
            "Please try again."
        )
        return state


FamilyContextOrchestrator = FamilyContextAgent
