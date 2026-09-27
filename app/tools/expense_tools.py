"""Controlled expense tools exposed to the Family Context Agent."""

from app.schemas.expense import (
    AddExpenseToolResult,
    ExpenseCreate,
    ExpenseSummaryQuery,
    ExpenseSummaryToolResult,
)
from app.services.expense import ExpenseService


async def add_expense(
    service: ExpenseService, payload: ExpenseCreate
) -> AddExpenseToolResult:
    """Record a fully specified household expense.

    The agent must obtain amount, category, and expense date before invoking this
    state-changing tool. Pydantic validation and service-level scope checks protect
    the database even when the tool is called outside the normal chat flow.
    """

    expense = await service.record_expense(payload)
    return AddExpenseToolResult(expense_id=expense.id)


async def get_expense_summary(
    service: ExpenseService, payload: ExpenseSummaryQuery
) -> ExpenseSummaryToolResult:
    """Return a filtered total calculated by the database."""

    summary = await service.get_summary(payload)
    return ExpenseSummaryToolResult(**summary.model_dump())
