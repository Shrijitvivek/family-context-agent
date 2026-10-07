import json
from datetime import date

from app.agents.prompts import SYSTEM_PROMPT
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

                # If the user did not provide an expense date,
                # use today's date.
                if (
                    tool_call.name == "add_expense"
                    and not arguments.get("expense_date")
                ):
                    arguments["expense_date"] = date.today().isoformat()

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


FamilyContextOrchestrator = FamilyContextAgent