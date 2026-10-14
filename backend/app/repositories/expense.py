"""Database access for household expenses."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ScopeViolationError
from app.models.expense import Expense
from app.models.family import Family
from app.models.family_member import FamilyMember
from app.repositories.query import build_filters
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

    @staticmethod
    def _filters(query: ExpenseSummaryQuery) -> list[ColumnElement[bool]]:
        return build_filters(
            Expense.family_id == query.family_id,
            Expense.member_id == query.member_id if query.member_id is not None else None,
            Expense.category == query.category if query.category is not None else None,
            Expense.expense_date >= query.start_date if query.start_date is not None else None,
            Expense.expense_date <= query.end_date if query.end_date is not None else None,
        )

    async def list_expenses(self, query: ExpenseSummaryQuery) -> list[Expense]:
        statement = (
            select(Expense)
            .where(*self._filters(query))
            .order_by(Expense.expense_date.desc(), Expense.created_at.desc())
        )
        return list((await self._session.scalars(statement)).all())

    async def summary(self, query: ExpenseSummaryQuery) -> ExpenseSummary:
        conditions = self._filters(query)

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
