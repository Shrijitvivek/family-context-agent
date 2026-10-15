
"""Orchestrate AI responses and family-context tool execution."""

import json

from app.agents.clarification import build_clarification
from app.agents.prompts import SYSTEM_PROMPT
from app.agents.state import AgentState
from app.clients.ai_model import AIModelClient
from app.core.config import get_settings
from app.tools.registry import ToolRegistry
from app.utils.dates import (
    resolve_commitment_due_date,
    resolve_expense_date,
)
import re
from decimal import Decimal, InvalidOperation


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

def _resolve_commitment_candidate(
    user_message: str,
    commitments: list[dict],
    *,
    allow_bare_amount: bool = False,
) -> str | None:
    """Return an ID only when explicit user details identify one record."""

    if not commitments:
        return None

    
    # Extract the requested amount without confusing it with the
    # new due date being requested.
    amount = None

    amount_patterns = [
        r"₹\s*([\d,]+(?:\.\d{1,2})?)",
        r"\b(?:bill|amount|commitment)\s+(?:of\s+)?"
        r"(?:₹\s*)?([\d,]+(?:\.\d{1,2})?)\b",
        r"\b([\d,]+(?:\.\d{1,2})?)\s+"
        r"(?:rupees|inr|bill|amount|commitment)\b",
    ]

    for pattern in amount_patterns:
        match = re.search(pattern, user_message, re.IGNORECASE)
        if match:
            try:
                amount = Decimal(match.group(1).replace(",", ""))
            except InvalidOperation:
                amount = None
            break

    # Allow a bare number only when the preceding assistant message
    # explicitly asked the user to identify an amount.
    if amount is None and allow_bare_amount:
        numbers = re.findall(
            r"(?<![\w.])\d[\d,]*(?:\.\d{1,2})?(?![\w.])",
            user_message,
        )

        # Do not guess when the reply contains several numbers.
        if len(numbers) == 1:
            try:
                amount = Decimal(numbers[0].replace(",", ""))
            except InvalidOperation:
                amount = None



    # Match an explicitly stated calendar date.
    date_match = re.search(
        r"\b("
        r"January|February|March|April|May|June|July|August|"
        r"September|October|November|December"
        r")\s+(\d{1,2})(?:,?\s+(\d{4}))?\b",
        user_message,
        re.IGNORECASE,
    )

    candidates = commitments

    if amount is not None:
        candidates = [
            item for item in candidates
            if item.get("amount") is not None
            and Decimal(str(item["amount"])) == amount
        ]

    if date_match:
        from datetime import date

        month_name, day, year = date_match.groups()
        month = date_match.group(1).lower()
        months = {
            "january": 1, "february": 2, "march": 3,
            "april": 4, "may": 5, "june": 6,
            "july": 7, "august": 8, "september": 9,
            "october": 10, "november": 11, "december": 12,
        }

        try:
            requested_month = months[month]
            requested_day = int(day)
            requested_year = int(year) if year else None
        except (KeyError, ValueError):
            return None

        def date_matches(item: dict) -> bool:
            raw_date = item.get("due_date")
            if not raw_date:
                return False

            try:
                stored_date = date.fromisoformat(str(raw_date)[:10])
            except ValueError:
                return False

            return (
                stored_date.month == requested_month
                and stored_date.day == requested_day
                and (
                    requested_year is None
                    or stored_date.year == requested_year
                )
            )

        # A date in a due-date correction may refer to the NEW date,
        # not the existing record. Use date filtering only if it narrows
        # the candidates; otherwise preserve the amount-based selection.
        dated_candidates = [
            item for item in candidates if date_matches(item)
        ]

        if dated_candidates:
            candidates = dated_candidates
        elif amount is None:
            return None

    if len(candidates) != 1:
        return None

    commitment_id = candidates[0].get("id")
    return str(commitment_id) if commitment_id else None

class FamilyContextAgent:
    def __init__(
        self,
        ai_client: AIModelClient,
        tool_registry: ToolRegistry,
    ) -> None:
        self.ai_client = ai_client
        self.tool_registry = tool_registry

    async def run(self, state: AgentState) -> AgentState:
        context_section = ""

        if state.household_context:
            context_section = f"""

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
        # Keep search evidence within this single agent run.
        commitment_search_records: list[dict] | None = None

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

                # Validate commitment selection before executing an update.
                if tool_call.name == "update_commitment":
                    requested_id = str(arguments.get("commitment_id", ""))

                    
                    
                    if commitment_search_records is None:
                        # Fetch fresh records if this run has not searched yet.
                        try:
                            search_result = await self.tool_registry.execute(
                                "search_commitments",
                                {
                                    "family_id": str(state.family_id),
                                    "status": "PENDING",
                                },
                            )
                        except Exception:
                            search_result = None

                        if (
                            not isinstance(search_result, dict)
                            or not search_result.get("success", False)
                            or not isinstance(
                                search_result.get("commitments"), list
                            )
                        ):
                            state.assistant_message = (
                                "I couldn't verify the matching commitments. "
                                "Please try again."
                            )
                            state.requires_clarification = True
                            return state

                        # IMPORTANT: Use records from the fresh search result,
                        # not the old commitment_search_records variable.
                        commitment_search_records = [
                            item
                            for item in search_result["commitments"]
                            if isinstance(item, dict)
                            and item.get("id") is not None
                        ]

                        state.tool_calls.append(
                            {
                                "name": "search_commitments",
                                "arguments": {
                                    "family_id": str(state.family_id),
                                    "status": "PENDING",
                                },
                            }
                        )
                        state.tool_results.append(
                            {
                                "tool": "search_commitments",
                                "result": search_result,
                            }
                        )

                    
                    # Normalize status values and keep only editable
                    # pending commitments.
                    def _get_record_field(record, field, default=None):
                        if isinstance(record, dict):
                            value = record.get(field, default)
                        else:
                            value = getattr(record, field, default)

                        if field == "status" and value is not None:
                            value = getattr(value, "value", value)

                        return value

                    commitment_search_records = [
                        item
                        for item in (commitment_search_records or [])
                        if str(
                            _get_record_field(item, "status", "")
                        ).upper().split(".")[-1] == "PENDING"
                    ]


                    if not commitment_search_records:
                        state.assistant_message = (
                            "I couldn't find a pending commitment to update. "
                            "Completed and cancelled commitments cannot be edited."
                        )
                        state.requires_clarification = True
                        return state



                    if len(commitment_search_records) == 1:
                        verified_id = str(commitment_search_records[0]["id"])

                        # Use the verified pending record, not an ID guessed by the model.
                        arguments["commitment_id"] = verified_id

                    elif len(commitment_search_records) > 1:
                        # Find the previous assistant message, excluding the current user reply.
                        history = list(state.history)

                        if (
                            history
                            and history[-1].get("role") == "user"
                            and history[-1].get("content", "").strip()
                            == state.user_message.strip()
                        ):
                            history.pop()

                        previous_assistant = next(
                            (
                                item
                                for item in reversed(history)
                                if item.get("role") == "assistant"
                            ),
                            None,
                        )

                        previous_question = (
                            previous_assistant.get("content", "").casefold()
                            if previous_assistant
                            else ""
                        )

                        # Enable bare-number parsing only when the previous assistant
                        # explicitly requested an amount or currency value.
                        allow_bare_amount = bool(
                            re.search(
                                r"\b(amount|how much|rupees|currency)\b",
                                previous_question,
                            )
                        )

                        verified_id = _resolve_commitment_candidate(
                            state.user_message,
                            commitment_search_records,
                            allow_bare_amount=allow_bare_amount,
                        )

                        if verified_id is None:
                            state.assistant_message = (
                                "I found multiple matching commitments. "
                                "Please specify the amount or existing due date "
                                "so I can identify the correct one."
                            )
                            state.requires_clarification = True
                            return state

                        # The unique candidate was selected from database search results.
                        # Do not trust a conflicting ID supplied by the model.
                        arguments["commitment_id"] = verified_id

                    else:
                        state.assistant_message = (
                            "I couldn't find a matching commitment. "
                            "Please specify which bill or task you mean."
                        )
                        state.requires_clarification = True
                        return state
                # Execute the tool after validation.
                try:
                    execute = getattr(
                        self.tool_registry,
                        "execute",
                        None,
                    )

                    if callable(execute):
                        result = await execute(
                            tool_call.name,
                            arguments,
                        ) # type: ignore
                    else:
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

                if tool_call.name == "search_commitments":
                    if isinstance(result, dict) and result.get("success", True):
                        records = result.get("commitments", [])

                        if isinstance(records, list):
                            commitment_search_records = [
                                item for item in records
                                if isinstance(item, dict) and item.get("id") is not None
                            ]
                        else:
                            commitment_search_records = None
                    else:
                        commitment_search_records = None

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
