"""Business operations backing the expense agent tools."""

from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import PersistenceError
from app.models.expense import Expense
from app.repositories.expense import ExpenseRepository
from app.schemas.expense import ExpenseCreate, ExpenseSummary, ExpenseSummaryQuery


class ExpenseService:
    def __init__(self, repository: ExpenseRepository) -> None:
        self._repository = repository

    async def record_expense(self, payload: ExpenseCreate) -> Expense:
        """Persist one validated expense after checking family/member ownership."""

        await self._repository.assert_scope(payload.family_id, payload.member_id)
        expense = Expense(
            family_id=payload.family_id,
            member_id=payload.member_id,
            amount=payload.amount,
            category=payload.category,
            merchant=payload.merchant,
            description=payload.description,
            expense_date=payload.expense_date,
            source_type=payload.source_type.value,
        )
        try:
            expense = await self._repository.add(expense)
            await self._repository.commit()
        except SQLAlchemyError as exc:
            await self._repository.rollback()
            raise PersistenceError("record the expense") from exc
        return expense

    async def get_summary(self, query: ExpenseSummaryQuery) -> ExpenseSummary:
        """Return a database aggregate, never a calculation from model context."""

        await self._repository.assert_scope(query.family_id, query.member_id)
        return await self._repository.summary(query)
