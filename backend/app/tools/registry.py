"""Validated registry for the implemented agent tools.

The remaining four planned MVP tools are intentionally not registered here yet:
an agent can only call a tool that has an implemented service behind it.
"""

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ValidationError

from app.core.exceptions import ToolInputValidationError
from app.schemas.commitment import (
    CommitmentCreate,
    CommitmentDependencyCreate,
    CommitmentUpdate,
    CreateCommitmentToolResult,
    CreateDependencyToolResult,
    GetFamilyPrioritiesQuery,
    GetFamilyPrioritiesToolResult,
    SearchCommitmentsQuery,
    SearchCommitmentsToolResult,
    UpdateCommitmentToolResult,
)
from app.schemas.expense import (
    AddExpenseToolResult,
    ExpenseCreate,
    ExpenseSummaryQuery,
    ExpenseSummaryToolResult,
)
from app.services.commitment import CommitmentService
from app.services.expense import ExpenseService
from app.tools.commitment_tools import (
    create_commitment,
    search_commitments,
    update_commitment,
)
from app.tools.dependency_tools import create_dependency
from app.tools.expense_tools import add_expense, get_expense_summary
from app.tools.priority_tools import get_family_priorities

ToolResult = (
    AddExpenseToolResult
    | ExpenseSummaryToolResult
    | CreateCommitmentToolResult
    | SearchCommitmentsToolResult
    | UpdateCommitmentToolResult
    | CreateDependencyToolResult
    | GetFamilyPrioritiesToolResult
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
    ) -> None:
        async def add_expense_handler(payload: BaseModel) -> AddExpenseToolResult:
            return await add_expense(expense_service, ExpenseCreate.model_validate(payload))

        async def expense_summary_handler(payload: BaseModel) -> ExpenseSummaryToolResult:
            return await get_expense_summary(
                expense_service, ExpenseSummaryQuery.model_validate(payload)
            )

        async def create_commitment_handler(payload: BaseModel) -> CreateCommitmentToolResult:
            return await create_commitment(
                commitment_service, CommitmentCreate.model_validate(payload)
            )

        async def search_commitments_handler(payload: BaseModel) -> SearchCommitmentsToolResult:
            return await search_commitments(
                commitment_service, SearchCommitmentsQuery.model_validate(payload)
            )

        async def update_commitment_handler(payload: BaseModel) -> UpdateCommitmentToolResult:
            return await update_commitment(
                commitment_service, CommitmentUpdate.model_validate(payload)
            )

        async def create_dependency_handler(payload: BaseModel) -> CreateDependencyToolResult:
            return await create_dependency(
                commitment_service, CommitmentDependencyCreate.model_validate(payload)
            )

        async def get_family_priorities_handler(
            payload: BaseModel,
        ) -> GetFamilyPrioritiesToolResult:
            return await get_family_priorities(
                commitment_service, GetFamilyPrioritiesQuery.model_validate(payload)
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
                description="Create a household bill, task, appointment, test, or deadline.",
                input_model=CommitmentCreate,
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
                description="Update an existing commitment's status, priority, or due date.",
                input_model=CommitmentUpdate,
                handler=update_commitment_handler,
            ),
            RegisteredTool(
                name="create_dependency",
                description="Create a dependency relationship between two commitments.",
                input_model=CommitmentDependencyCreate,
                handler=create_dependency_handler,
            ),
            RegisteredTool(
                name="get_family_priorities",
                description="Get upcoming and high-priority commitments for the family.",
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
            errors = exc.errors() if isinstance(exc, ValidationError) else []
            raise ToolInputValidationError(
                f"Invalid input for '{name}'.", details={"tool_name": name, "errors": errors}
            ) from exc
        result = await tool.handler(payload)
        return result.model_dump(mode="json")
