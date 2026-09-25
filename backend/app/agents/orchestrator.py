"""Primary Family Context Agent orchestrator."""

from typing import Any

from app.agents.clarification import build_clarification
from app.schemas.agent import AgentContext, AgentDecision


STATE_CHANGING_TOOLS = {
    "add_expense",
    "create_commitment",
    "update_commitment",
    "create_dependency",
}


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

        # The family context comes from the application, not the user.
        arguments = dict(arguments)
        arguments.setdefault("family_id", str(context.family_id))

        if context.member_id is not None:
            arguments.setdefault("member_id", str(context.member_id))

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