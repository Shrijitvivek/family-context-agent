"""Validated registry for the agent tools.

Every tool is a thin wrapper over the same service method the REST API uses, so
the agent and the UI always follow the same business rules. An agent can only call
a tool that is registered here.
"""

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from typing import Any

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, ValidationError

from app.core.exceptions import FamilyContextError, ToolInputValidationError
from app.schemas.commitment import (
    CommitmentUpdate,
    GetFamilyPrioritiesQuery,
    SearchCommitmentsQuery,
)
from app.schemas.expense import ExpenseCreate, ExpenseSummaryQuery
from app.services.commitment import CommitmentService
from app.services.document import DocumentService
from app.services.expense import ExpenseService
from app.services.priority import PriorityService
from app.tools.commitment_tools import (
    CreateCommitmentInput,
    CreateCommitmentResult,
    SearchCommitmentsResult,
    UpdateCommitmentResult,
    create_commitment,
    search_commitments,
    update_commitment,
)
from app.tools.dependency_tools import (
    CreateDependencyInput,
    CreateDependencyResult,
    create_dependency,
)
from app.tools.expense_tools import (
    AddExpenseResult,
    ExpenseSummaryResult,
    add_expense,
    get_expense_summary,
)
from app.tools.priority_tools import GetFamilyPrioritiesResult, get_family_priorities

ToolResult = (
    AddExpenseResult
    | ExpenseSummaryResult
    | CreateCommitmentResult
    | SearchCommitmentsResult
    | UpdateCommitmentResult
    | CreateDependencyResult
    | GetFamilyPrioritiesResult
)
ToolHandler = Callable[[BaseModel], Awaitable[ToolResult]]


@dataclass(frozen=True)
class RegisteredTool:
    name: str
    description: str
    input_model: type[BaseModel]
    handler: ToolHandler

    def model_definition(self) -> dict[str, Any]:
        """Return an OpenAI/NVIDIA-compatible function-tool description."""

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_model.model_json_schema(),
            },
        }


class ToolRegistry:
    """Binds request-scoped services to the seven Family Context tools."""

    def __init__(
        self,
        expense_service: ExpenseService,
        commitment_service: CommitmentService,
        priority_service: PriorityService,
        document_service: DocumentService | None = None,
    ) -> None:
        async def add_expense_handler(payload: BaseModel) -> AddExpenseResult:
            return await add_expense(expense_service, ExpenseCreate.model_validate(payload))

        async def expense_summary_handler(payload: BaseModel) -> ExpenseSummaryResult:
            return await get_expense_summary(
                expense_service, ExpenseSummaryQuery.model_validate(payload)
            )

        async def create_commitment_handler(payload: BaseModel) -> CreateCommitmentResult:
            return await create_commitment(
                commitment_service,
                CreateCommitmentInput.model_validate(payload),
                document_service,
            )

        async def search_commitments_handler(payload: BaseModel) -> SearchCommitmentsResult:
            return await search_commitments(
                commitment_service, SearchCommitmentsQuery.model_validate(payload)
            )

        async def update_commitment_handler(payload: BaseModel) -> UpdateCommitmentResult:
            return await update_commitment(
                commitment_service, CommitmentUpdate.model_validate(payload)
            )

        async def create_dependency_handler(payload: BaseModel) -> CreateDependencyResult:
            return await create_dependency(
                commitment_service, CreateDependencyInput.model_validate(payload)
            )

        async def get_family_priorities_handler(
            payload: BaseModel,
        ) -> GetFamilyPrioritiesResult:
            return await get_family_priorities(
                priority_service, GetFamilyPrioritiesQuery.model_validate(payload)
            )

        definitions = (
            RegisteredTool(
                name="add_expense",
                description="Record one fully specified household expense.",
                input_model=ExpenseCreate,
                handler=add_expense_handler,
            ),
            RegisteredTool(
                name="get_expense_summary",
                description=(
                    "Calculate household expense totals for an optional category and date range."
                ),
                input_model=ExpenseSummaryQuery,
                handler=expense_summary_handler,
            ),
            RegisteredTool(
                name="create_commitment",
                description=(
                    "Create a household bill, task, appointment, test, or deadline. Bills, "
                    "appointments, lab tests, deadlines, and renewals need a due_date. To save "
                    "an uploaded document the user has confirmed, pass its document_id; fields "
                    "you omit are taken from the document's extraction. If similar items are "
                    "returned, ask the user before retrying with confirmed_new=true."
                ),
                input_model=CreateCommitmentInput,
                handler=create_commitment_handler,
            ),
            RegisteredTool(
                name="search_commitments",
                description="Search for existing family commitments matching specific filters.",
                input_model=SearchCommitmentsQuery,
                handler=search_commitments_handler,
            ),
            RegisteredTool(
                name="update_commitment",
                description=(
                    "Complete, cancel, reprioritise, or reschedule an existing commitment. Find "
                    "its commitment_id with search_commitments first. Completed and cancelled "
                    "items cannot be changed."
                ),
                input_model=CommitmentUpdate,
                handler=update_commitment_handler,
            ),
            RegisteredTool(
                name="create_dependency",
                description=(
                    "Record that the source commitment must be completed before the target "
                    "commitment (relationship_type MUST_COMPLETE_BEFORE)."
                ),
                input_model=CreateDependencyInput,
                handler=create_dependency_handler,
            ),
            RegisteredTool(
                name="get_family_priorities",
                description=(
                    "Get what needs the family's attention now: overdue items, items due "
                    "soon, and unfinished prerequisites, each with the reason."
                ),
                input_model=GetFamilyPrioritiesQuery,
                handler=get_family_priorities_handler,
            ),
        )
        self._tools = {tool.name: tool for tool in definitions}

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(self._tools)

    def definitions(self) -> list[dict[str, Any]]:
        return [tool.model_definition() for tool in self._tools.values()]

    async def dispatch(self, name: str, arguments: Mapping[str, Any]) -> dict[str, Any]:
        """Validate agent-supplied JSON and execute only a registered tool."""

        tool = self._tools.get(name)
        if tool is None:
            raise ToolInputValidationError(
                f"Tool '{name}' is not available.", details={"tool_name": name}
            )
        try:
            payload = tool.input_model.model_validate(dict(arguments))
        except (TypeError, ValidationError) as exc:
            errors = (
                exc.errors(include_url=False, include_context=False)
                if isinstance(exc, ValidationError)
                else []
            )
            raise ToolInputValidationError(
                f"Invalid input for '{name}'.", details={"tool_name": name, "errors": errors}
            ) from exc
        result = await tool.handler(payload)
        return result.model_dump(mode="json")

    async def execute(self, name: str, arguments: Mapping[str, Any]) -> dict[str, Any]:
        """Like ``dispatch``, but returns domain errors in one stable failure shape.

        ``{"success": false, "error": {"code", "message", "details"}}`` keeps the
        candidates of a duplicate or the missing fields of an invalid call visible
        to the model, so it can ask a precise clarification question.
        """

        try:
            return await self.dispatch(name, arguments)
        except FamilyContextError as exc:
            return {
                "success": False,
                "error": {
                    "code": exc.code,
                    "message": str(exc),
                    "details": jsonable_encoder(exc.details),
                },
            }
