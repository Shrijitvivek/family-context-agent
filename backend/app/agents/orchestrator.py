import json
from datetime import date
from typing import Any
from uuid import UUID

from app.agents.clarification import build_clarification
from app.agents.prompts import SYSTEM_PROMPT
from app.agents.state import AgentState
from app.clients.ai_model import AIModelClient
from app.core.config import get_settings
from app.core.exceptions import FamilyContextError, ToolInputValidationError
from app.tools.registry import ToolRegistry, ToolSideEffect
from app.utils.dates import resolve_commitment_date, resolve_expense_date


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

def _mutation_failure_message(failures: dict[str, str]) -> str:
    if len(failures) == 1:
        tool_name, failure_code = next(iter(failures.items()))
        if failure_code == "possible_duplicate_commitment":
            return (
                "A matching commitment already exists. Please confirm whether "
                "it is the same commitment before I make changes."
            )
        if failure_code == "invalid_tool_input":
            if tool_name == "add_expense":
                return "I need to clarify the expense details before I can record it."
            if tool_name == "create_commitment":
                return "I need to clarify that request."
            if tool_name == "update_commitment":
                return (
                    "I couldn't identify the commitment to update. "
                    "Please clarify which commitment you mean."
                )
            return "I need to clarify that request."

        action = {
            "add_expense": "expense",
            "create_commitment": "commitment",
            "update_commitment": "commitment update",
            "create_dependency": "dependency",
        }[tool_name]
        return (
            f"The requested {action} was not completed successfully. "
            "I can't confirm that it was saved; please check your household "
            "records before retrying."
        )

    return (
        "At least one requested change was not completed successfully. "
        "I can't confirm that it was saved; please check your household "
        "records before retrying."
    )


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

        # Add attached document context for the AI.
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
        failed_mutations: dict[str, str] = {}

        for _ in range(max_tool_rounds):
            response = await self.ai_client.chat(
                messages=messages,
                tools=tool_definitions,
            )

            # No tool requested by the AI.
            # Return the normal assistant response.
            if not response.tool_calls:
                state.assistant_message = (
                    _mutation_failure_message(failed_mutations)
                    if failed_mutations
                    else response.content or "I couldn't generate a response."
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

                # Application-owned context
                arguments["family_id"] = str(state.family_id)

                if tool_call.name in {"add_expense", "create_commitment"}:
                    if state.member_id is not None:
                        arguments["member_id"] = str(state.member_id)

                try:
                    failure_message = None
                    date_clarification = False
                    if (
                        tool_call.name == "update_commitment"
                        and hasattr(self.tool_registry, "resolve_update_target")
                    ):
                        arguments["commitment_id"] = str(
                            await self.tool_registry.resolve_update_target(
                                family_id=state.family_id,
                                member_id=state.member_id,
                                reference=state.user_message,
                                model_selected_id=UUID(
                                    str(arguments["commitment_id"])
                                ),
                            )
                        )

                    if tool_call.name == "add_expense":
                        resolved_date = resolve_expense_date(
                            _expense_date_source(state),
                            get_settings().family_timezone,
                        )
                        arguments["expense_date"] = resolved_date.isoformat()

                    if (
                        tool_call.name == "create_commitment"
                        and arguments.get("document_id") is None
                    ):
                        try:
                            resolved_date = resolve_commitment_date(
                                state.user_message,
                                state.metadata.get("family_timezone")
                                or get_settings().family_timezone,
                            )
                        except ValueError as exc:
                            date_clarification = True
                            raise ToolInputValidationError(
                                "I couldn't safely resolve the requested commitment date. "
                                "Please clarify the date."
                            ) from exc

                        # Never persist a date invented by the model when the
                        # user did not state a date in this request.
                        arguments["due_date"] = (
                            resolved_date.isoformat() if resolved_date else None
                        )

                        clarification = build_clarification(
                            tool_call.name,
                            arguments,
                        )
                        if clarification is not None:
                            state.requires_clarification = True
                            state.assistant_message = (
                                clarification.clarification.question
                                if clarification.clarification is not None
                                else "When is this bill or commitment due?"
                            )
                            return state

                    execute = getattr(
                        self.tool_registry,
                        "execute",
                        None,
                    )

                    if callable(execute):
                        result = await execute(
                            tool_call.name,
                            arguments,
                        )  # type: ignore
                    else:
                        result = await self.tool_registry.dispatch(
                            tool_call.name,
                            arguments,
                        )

                    failure_code = None
                    if isinstance(result, dict) and result.get("success") is False:
                        error = result.get("error")
                        if isinstance(error, dict):
                            failure_code = error.get("code")
                            failure_message = error.get("message")
                except Exception as exc:
                    result = {
                        "success": False,
                        "error": str(exc),
                    }
                    failure_code = (
                        exc.code
                        if isinstance(exc, FamilyContextError)
                        else "tool_execution_failed"
                    )
                    failure_message = str(exc)

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

                is_mutating = getattr(
                    self.tool_registry,
                    "side_effect",
                    lambda _name: ToolSideEffect.MUTATION,
                )(tool_call.name) == ToolSideEffect.MUTATION
                if (
                    is_mutating
                    and isinstance(result, dict)
                    and result.get("success") is False
                ):
                    failed_mutations[tool_call.name] = (
                        failure_code or "tool_execution_failed"
                    )
                    state.requires_clarification = (
                        failure_code == "ambiguous_commitment_reference"
                        or date_clarification
                    )
                    state.assistant_message = (
                        failure_message
                        if state.requires_clarification and failure_message
                        else _mutation_failure_message(failed_mutations)
                    )
                    return state

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
            _mutation_failure_message(failed_mutations)
            if failed_mutations
            else "I couldn't complete the request safely. Please try again."
        )
        return state


FamilyContextOrchestrator = FamilyContextAgent
