"""Database access for household expenses."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ScopeViolationError
from app.models.expense import Expense
from app.models.family import Family
from app.models.family_member import FamilyMember
from app.schemas.expense import ExpenseSummary, ExpenseSummaryQuery


class ExpenseRepository:
    """Queries are intentionally family-scoped before returning any data."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def assert_scope(self, family_id: UUID, member_id: UUID | None = None) -> None:
        family = await self._session.scalar(select(Family.id).where(Family.id == family_id))
        if family is None:
            raise NotFoundError("Family", family_id)

        if member_id is not None:
            member_family_id = await self._session.scalar(
                select(FamilyMember.family_id).where(FamilyMember.id == member_id)
            )
            if member_family_id is None:
                raise NotFoundError("Family member", member_id)
            if member_family_id != family_id:
                raise ScopeViolationError("Family member", member_id, family_id)

    async def add(self, expense: Expense) -> Expense:
        self._session.add(expense)
        await self._session.flush()
        await self._session.refresh(expense)
        return expense

    async def summary(self, query: ExpenseSummaryQuery) -> ExpenseSummary:
        conditions = [Expense.family_id == query.family_id]
        if query.member_id is not None:
            conditions.append(Expense.member_id == query.member_id)
        if query.category is not None:
            conditions.append(Expense.category == query.category)
        if query.start_date is not None:
            conditions.append(Expense.expense_date >= query.start_date)
        if query.end_date is not None:
            conditions.append(Expense.expense_date <= query.end_date)

        statement = select(
            func.coalesce(func.sum(Expense.amount), Decimal("0.00")).label("total"),
            func.count(Expense.id).label("transaction_count"),
        ).where(*conditions)
        row = (await self._session.execute(statement)).one()
        return ExpenseSummary(
            total=Decimal(str(row.total)),
            transaction_count=int(row.transaction_count),
            category=query.category,
            start_date=query.start_date,
            end_date=query.end_date,
        )

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
