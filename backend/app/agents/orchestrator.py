"""Primary Family Context Agent orchestrator."""

import json
from datetime import date
from typing import TYPE_CHECKING, Any

from app.agents.clarification import build_clarification
from app.agents.prompts import SYSTEM_PROMPT
from app.core.exceptions import DuplicateCommitmentError, ToolInputValidationError
from app.schemas.agent import AgentContext, AgentDecision, AgentTurnResult

if TYPE_CHECKING:
    # Imported only for type hints, to avoid a circular import at runtime.
    from app.clients.ai_model import AIModelClient


STATE_CHANGING_TOOLS = {
    "add_expense",
    "create_commitment",
    "update_commitment",
    "create_dependency",
}

# Tools where member_id means "who this belongs to".
# In search/summary tools member_id is a *filter*, so it must not be added
# automatically: "How much did we spend?" is a whole-household question.
MEMBER_OWNED_TOOLS = {
    "add_expense",
    "create_commitment",
}


def decision_from_model_tool_call(
    tool_name: str,
    raw_arguments: str | dict[str, Any] | None,
) -> AgentDecision:
    """
    Convert a tool call from an OpenAI-compatible model into an AgentDecision.

    NVIDIA/Nebius models send tool arguments as a JSON string, for example:
    '{"amount": 500, "category": "groceries"}'.
    If the arguments cannot be read, ask the user instead of guessing.
    """

    if raw_arguments is None or raw_arguments == "":
        return AgentDecision.tool(name=tool_name, arguments={})

    if isinstance(raw_arguments, dict):
        return AgentDecision.tool(name=tool_name, arguments=raw_arguments)

    try:
        arguments = json.loads(raw_arguments)
    except (TypeError, ValueError):
        arguments = None

    if not isinstance(arguments, dict):
        return AgentDecision.ask(
            question=(
                "I couldn't understand the details of that request. "
                "Could you say it again?"
            ),
            reason=f"Model returned unreadable arguments for {tool_name}.",
        )

    return AgentDecision.tool(name=tool_name, arguments=arguments)


class FamilyContextOrchestrator:
    """Coordinates model decisions with clarification and tool safety."""

    def __init__(self, tool_registry) -> None:
        self._tool_registry = tool_registry

    def available_tools(self) -> list[dict[str, Any]]:
        """Return tool definitions that can be supplied to the AI model."""

        return self._tool_registry.definitions()

    async def prepare_tool_call(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        context: AgentContext,
    ) -> AgentDecision:
        """
        Validate the model's intended action before any state change.

        This method does not execute the tool.
        It only decides whether the request is ready.
        """

        # The family context comes from the application, not the model.
        # Always overwrite so the AI cannot target another family's data.
        arguments = dict(arguments)
        arguments["family_id"] = str(context.family_id)

        # The speaking member owns new expenses and commitments.
        if context.member_id is not None and tool_name in MEMBER_OWNED_TOOLS:
            arguments["member_id"] = str(context.member_id)

        # Make sure the AI cannot call a tool that is not registered.
        if tool_name not in self._tool_registry.names:
            return AgentDecision.ask(
                question=(
                    "I couldn't determine a supported action for that request. "
                    "Could you rephrase what you'd like me to do?"
                ),
                reason=f"Unknown tool requested: {tool_name}",
            )

        # State-changing tools must pass clarification checks first.
        if tool_name in STATE_CHANGING_TOOLS:
            clarification = build_clarification(
                tool_name,
                arguments,
            )

            if clarification is not None:
                return clarification

        return AgentDecision.tool(
            name=tool_name,
            arguments=arguments,
        )

    async def execute_tool(
        self,
        decision: AgentDecision,
    ) -> dict[str, Any]:
        """Execute an already-approved tool call."""

        if decision.action != "tool_call":
            raise ValueError("Only tool_call decisions can be executed.")

        if decision.tool_call is None:
            raise ValueError("tool_call decision is missing tool information.")

        return await self._tool_registry.dispatch(
            decision.tool_call.tool_name,
            decision.tool_call.arguments,
        )

    async def handle_decision(
        self,
        decision: AgentDecision,
        context: AgentContext,
    ) -> AgentTurnResult:
        """
        Single safe entry point for any decision made by the AI model.

        - response: returned unchanged.
        - clarification: returned unchanged.
        - tool_call: checked by prepare_tool_call() first, and executed
          only if it is approved.
        """

        # Replies and questions do not touch any tool.
        if decision.action != "tool_call":
            return AgentTurnResult(decision=decision)

        # A tool_call with no tool details cannot be run safely.
        if decision.tool_call is None:
            return AgentTurnResult(
                decision=AgentDecision.ask(
                    question=(
                        "I couldn't determine a supported action for that request. "
                        "Could you rephrase what you'd like me to do?"
                    ),
                    reason="Model returned a tool_call without tool information.",
                )
            )

        # Every tool request goes through the safety gate first.
        approved = await self.prepare_tool_call(
            decision.tool_call.tool_name,
            decision.tool_call.arguments,
            context,
        )

        # The gate asked a question instead of approving the tool.
        if approved.action != "tool_call":
            return AgentTurnResult(decision=approved)

        try:
            tool_result = await self.execute_tool(approved)

        except DuplicateCommitmentError as exc:
            # The tool found a matching commitment: ask instead of creating a copy.
            return AgentTurnResult(
                decision=AgentDecision.ask(
                    question=(
                        "This looks like a commitment you already have. "
                        "Is this a new one, or did you mean the existing one?"
                    ),
                    reason=exc.code,
                ),
                tool_result={
                    "error": exc.code,
                    "candidates": exc.details.get("candidates", []),
                },
            )

        except ToolInputValidationError as exc:
            # A value was rejected by the tool (for example, an amount of 0).
            fields = [
                ".".join(str(part) for part in error.get("loc", ()))
                for error in exc.details.get("errors", [])
            ]
            return AgentTurnResult(
                decision=AgentDecision.ask(
                    question=(
                        "Some of those details don't look right. "
                        "Could you check them and tell me again?"
                    ),
                    missing_fields=fields,
                    reason=exc.code,
                ),
                tool_result={"error": exc.code, "fields": fields},
            )

        return AgentTurnResult(
            decision=approved,
            tool_result=tool_result,
        )

    def build_messages(
        self,
        user_message: str,
        history: list[dict[str, Any]] | None = None,
        today: date | None = None,
    ) -> list[dict[str, Any]]:
        """Build the message list sent to the model for one turn."""

        today = today or date.today()
        system_content = (
            f"{SYSTEM_PROMPT.strip()}\n\n"
            f"Today's date is {today.isoformat()}. "
            "Use it to convert words like 'today' or 'yesterday' into dates."
        )

        return [
            {"role": "system", "content": system_content},
            *(history or []),
            {"role": "user", "content": user_message},
        ]

    async def run_turn(
        self,
        user_message: str,
        context: AgentContext,
        model_client: "AIModelClient",
        history: list[dict[str, Any]] | None = None,
        today: date | None = None,
    ) -> AgentTurnResult:
        """
        Run one full agent turn:
        user message -> AI model -> safety gate -> tool (if approved).

        `history` holds earlier messages of this conversation, so the model
        can combine a clarification answer with the original request.
        Saving messages to the database is left to the chat service.
        """

        messages = self.build_messages(user_message, history, today)
        decision = await model_client.decide(messages, self.available_tools())
        return await self.handle_decision(decision, context)