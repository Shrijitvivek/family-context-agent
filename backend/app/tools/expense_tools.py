"""Controlled expense tools exposed to the Family Context Agent."""

from datetime import date
from decimal import Decimal
from typing import Literal

from app.schemas.expense import (
    AddExpenseToolResult,
    ExpenseCreate,
    ExpenseSummaryQuery,
    ExpenseSummaryToolResult,
)
from app.services.expense import ExpenseService


class AddExpenseResult(AddExpenseToolResult):
    amount: Decimal
    category: str
    expense_date: date


class ExpenseSummaryResult(ExpenseSummaryToolResult):
    success: Literal[True] = True
    message: str


async def add_expense(
    service: ExpenseService, payload: ExpenseCreate
) -> AddExpenseResult:
    """Record a fully specified household expense.

    The agent must obtain amount and category before invoking this state-changing
    tool. The chat backend supplies today's date in the family's configured timezone
    when the user does not specify a date. Pydantic validation and service-level
    scope checks protect the database even when called outside the normal chat flow.
    """

    expense = await service.record_expense(payload)
    return AddExpenseResult(
        expense_id=expense.id,
        amount=expense.amount,
        category=expense.category,
        expense_date=expense.expense_date,
        message=(
            f"Recorded {expense.amount} for {expense.category} "
            f"on {expense.expense_date.isoformat()}."
        ),
    )


async def get_expense_summary(
    service: ExpenseService, payload: ExpenseSummaryQuery
) -> ExpenseSummaryResult:
    """Return a filtered total calculated by the database."""

    summary = await service.get_summary(payload)
    scope = summary.category or "all categories"
    if summary.transaction_count == 0:
        message = f"No expenses were found for {scope} in that period."
    else:
        plural = "s" if summary.transaction_count != 1 else ""
        message = (
            f"Total for {scope}: {summary.total} "
            f"across {summary.transaction_count} expense{plural}."
        )
    return ExpenseSummaryResult(**summary.model_dump(), message=message)
