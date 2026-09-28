"""Chat workflow: persist the turn, run the agent, and reply from real results.

The user's message is committed before the agent runs, so a failed tool (which
rolls back its own transaction) cannot erase the conversation. Success messages
are built from the tool's returned data, never from the model's own claims.
Priority refresh after a change is handled by the services behind the tools.
"""

from collections.abc import Callable
from datetime import date
from typing import Any
from uuid import UUID

from app.agents.orchestrator import FamilyContextOrchestrator
from app.clients.ai_model import ModelClient
from app.core.constants import MessageRole
from app.core.exceptions import AIModelError, FamilyContextError
from app.models.message import Message
from app.repositories.conversation import ConversationRepository
from app.schemas.agent import AgentContext, AgentTurnResult
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.context import ContextService

HISTORY_LIMIT = 12
MAX_LISTED = 5


def _list_commitments(commitments: list[dict[str, Any]], empty: str) -> str:
    if not commitments:
        return empty
    lines = []
    for c in commitments[:MAX_LISTED]:
        due = f" (due {c['due_date']})" if c.get("due_date") else ""
        lines.append(f"- {c['title']}{due}")
    more = len(commitments) - MAX_LISTED
    if more > 0:
        lines.append(f"...and {more} more.")
    return "\n".join(lines)


def describe_tool_result(tool_name: str, arguments: dict[str, Any], result: dict[str, Any]) -> str:
    """Deterministic confirmation text for a successful tool call."""

    if tool_name == "add_expense":
        text = f"Recorded ₹{arguments.get('amount')} for {arguments.get('category')}"
        return f"{text} on {arguments.get('expense_date')}."
    if tool_name == "get_expense_summary":
        scope = f" on {result['category']}" if result.get("category") else ""
        if result.get("start_date") or result.get("end_date"):
            scope += f" from {result.get('start_date') or 'the start'}"
            scope += f" to {result.get('end_date') or 'today'}"
        count = result.get("transaction_count", 0)
        return f"You spent ₹{result.get('total')}{scope} across {count} transaction(s)."
    if tool_name == "create_commitment":
        due = f", due {arguments['due_date']}" if arguments.get("due_date") else ""
        return f"Added “{arguments.get('title')}”{due}."
    if tool_name == "search_commitments":
        return _list_commitments(
            result.get("commitments", []), "I couldn't find any matching commitments."
        )
    if tool_name == "update_commitment":
        return f"Updated. That commitment is now {str(result.get('status', '')).lower()}."
    if tool_name == "create_dependency":
        return "Linked them: the first must be completed before the second."
    if tool_name == "get_family_priorities":
        items = result.get("items", [])
        if not items:
            return "Nothing needs attention right now."
        lines = [f"- {item['message']}" for item in items[:MAX_LISTED]]
        if len(items) > MAX_LISTED:
            lines.append(f"...and {len(items) - MAX_LISTED} more.")
        return "\n".join(lines)
    return "Done."


class ChatService:
    def __init__(
        self,
        conversations: ConversationRepository,
        context: ContextService,
        orchestrator: FamilyContextOrchestrator,
        model: ModelClient,
        today: Callable[[], date],
    ) -> None:
        self._conversations = conversations
        self._context = context
        self._orchestrator = orchestrator
        self._model = model
        self._today = today

    async def history(self, family_id: UUID, conversation_id: UUID) -> list[Message]:
        await self._conversations.get(family_id, conversation_id)
        return await self._conversations.recent_messages(conversation_id, limit=200)

    async def handle(self, request: ChatRequest) -> ChatResponse:
        household = await self._context.build(request.family_id, request.member_id)

        if request.conversation_id is not None:
            conversation = await self._conversations.get(
                request.family_id, request.conversation_id
            )
        else:
            conversation = await self._conversations.create(request.family_id)

        previous = await self._conversations.recent_messages(conversation.id, HISTORY_LIMIT)
        await self._conversations.add_message(
            conversation.id, MessageRole.USER.value, request.message
        )
        await self._conversations.commit()

        history = [
            {"role": "system", "content": household.to_prompt()},
            *({"role": m.role, "content": m.content} for m in previous),
        ]
        response = await self._run_agent(request, conversation.id, history, self._today())

        await self._conversations.add_message(
            conversation.id, MessageRole.ASSISTANT.value, response.reply
        )
        await self._conversations.commit()
        return response

    async def _run_agent(
        self,
        request: ChatRequest,
        conversation_id: UUID,
        history: list[dict[str, Any]],
        today: date,
    ) -> ChatResponse:
        base = {"conversation_id": conversation_id}
        try:
            result: AgentTurnResult = await self._orchestrator.run_turn(
                request.message,
                AgentContext(
                    family_id=request.family_id,
                    member_id=request.member_id,
                    conversation_id=conversation_id,
                ),
                self._model,  # type: ignore[arg-type]
                history=history,
                today=today,
            )
        except AIModelError:
            return ChatResponse(
                **base,
                action="error",
                reply="I can't reach the assistant right now. Nothing was changed. "
                "Please try again in a moment.",
            )
        except FamilyContextError as exc:
            # e.g. a dependency cycle, an unknown commitment, or a failed save.
            await self._conversations.rollback()
            return ChatResponse(
                **base,
                action="error",
                reply=f"{exc} Nothing was changed.",
                tool_result={"error": exc.code, **exc.details},
            )

        decision = result.decision
        if decision.action == "clarification" and decision.clarification is not None:
            return ChatResponse(
                **base,
                action="clarification",
                reply=decision.clarification.question,
                missing_fields=decision.clarification.missing_fields,
                tool_result=result.tool_result,
            )
        if decision.action == "tool_call" and decision.tool_call is not None:
            call = decision.tool_call
            tool_result = result.tool_result or {}
            return ChatResponse(
                **base,
                action="tool_call",
                reply=describe_tool_result(call.tool_name, call.arguments, tool_result),
                tool_name=call.tool_name,
                tool_result=result.tool_result,
            )
        return ChatResponse(**base, action="response", reply=decision.response or "")
