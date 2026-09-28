"""Expense endpoints. Totals are always calculated by the database."""

from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.dependencies import ExpenseServiceDep
from app.schemas.expense import ExpenseCreate, ExpenseRead, ExpenseSummary, ExpenseSummaryQuery

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.post("", response_model=ExpenseRead, status_code=status.HTTP_201_CREATED)
async def create_expense(payload: ExpenseCreate, service: ExpenseServiceDep):
    return await service.record_expense(payload)


@router.get("", response_model=list[ExpenseRead])
async def list_expenses(
    query: Annotated[ExpenseSummaryQuery, Query()], service: ExpenseServiceDep
):
    return await service.list_expenses(query)


@router.get("/summary", response_model=ExpenseSummary)
async def get_expense_summary(
    query: Annotated[ExpenseSummaryQuery, Query()], service: ExpenseServiceDep
):
    return await service.get_summary(query)
