"""Validated inputs and outputs for expense tools."""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.constants import SourceType


def _normalise_category(value: str) -> str:
    normalised = "_".join(value.strip().upper().split())
    if not normalised:
        raise ValueError("category cannot be blank")
    return normalised


class ExpenseCreate(BaseModel):
    """The complete fact set the agent must obtain before recording an expense."""

    family_id: UUID
    member_id: UUID | None = None
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    category: str = Field(min_length=1, max_length=50)
    merchant: str | None = Field(default=None, max_length=150)
    description: str | None = Field(default=None, max_length=2_000)
    expense_date: date
    source_type: SourceType = SourceType.TEXT

    @field_validator("category")
    @classmethod
    def normalise_category(cls, value: str) -> str:
        return _normalise_category(value)

    @field_validator("merchant", "description", mode="before")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class ExpenseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    family_id: UUID
    member_id: UUID | None
    amount: Decimal
    category: str
    merchant: str | None
    description: str | None
    expense_date: date
    source_type: SourceType
    created_at: datetime


class ExpenseSummaryQuery(BaseModel):
    """Filters for a database-calculated expense total.

    Dates are inclusive. A category is optional so the same controlled tool can
    answer either a category question or a whole-household question.
    """

    family_id: UUID
    category: str | None = Field(default=None, max_length=50)
    member_id: UUID | None = None
    start_date: date | None = None
    end_date: date | None = None

    @field_validator("category")
    @classmethod
    def normalise_optional_category(cls, value: str | None) -> str | None:
        return _normalise_category(value) if value is not None else None

    @model_validator(mode="after")
    def check_date_range(self) -> "ExpenseSummaryQuery":
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("start_date must be on or before end_date")
        return self


class ExpenseSummary(BaseModel):
    total: Decimal
    transaction_count: int = Field(ge=0)
    category: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class AddExpenseToolResult(BaseModel):
    success: Literal[True] = True
    expense_id: UUID
    message: str = "Expense recorded"


class ExpenseSummaryToolResult(ExpenseSummary):
    """Compact result returned to the agent by ``get_expense_summary``."""
