# # """Expense repository.
# # 
# TODO:
# - Implement expense writes, filtered listings, and SQL aggregate summaries.
# - Let PostgreSQL calculate totals and counts.
# """
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.expense import Expense


class ExpenseRepository:
    """Database operations for Expense."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        family_id: UUID,
        amount: Decimal,
        category: str,
        expense_date: date,
        member_id: UUID | None = None,
        merchant: str | None = None,
        description: str | None = None,
        source: str | None = None,
    ) -> Expense:

        expense = Expense(
            family_id=family_id,
            member_id=member_id,
            amount=amount,
            category=category,
            merchant=merchant,
            expense_date=expense_date,
            description=description,
            source=source,
        )

        self.session.add(expense)
        await self.session.flush()
        await self.session.refresh(expense)

        return expense

    async def get_by_id(
        self,
        expense_id: UUID,
    ) -> Expense | None:

        result = await self.session.execute(
            select(Expense).where(Expense.id == expense_id)
        )

        return result.scalar_one_or_none()

    async def get_by_family(
        self,
        family_id: UUID,
    ) -> list[Expense]:

        result = await self.session.execute(
            select(Expense)
            .where(Expense.family_id == family_id)
            .order_by(Expense.expense_date.desc())
        )

        return list(result.scalars().all())

    async def get_by_member(
        self,
        member_id: UUID,
    ) -> list[Expense]:

        result = await self.session.execute(
            select(Expense)
            .where(Expense.member_id == member_id)
            .order_by(Expense.expense_date.desc())
        )

        return list(result.scalars().all())

    async def update(
        self,
        expense_id: UUID,
        **values,
    ) -> Expense | None:

        expense = await self.get_by_id(expense_id)

        if expense is None:
            return None

        for field, value in values.items():
            if value is not None:
                setattr(expense, field, value)

        await self.session.flush()
        await self.session.refresh(expense)

        return expense

    async def delete(
        self,
        expense_id: UUID,
    ) -> bool:

        expense = await self.get_by_id(expense_id)

        if expense is None:
            return False

        await self.session.delete(expense)
        await self.session.flush()

        return True

    async def get_total_for_family(
        self,
        family_id: UUID,
    ) -> Decimal:

        result = await self.session.execute(
            select(func.coalesce(func.sum(Expense.amount), 0))
            .where(Expense.family_id == family_id)
        )

        return result.scalar_one()

    async def get_count_for_family(
        self,
        family_id: UUID,
    ) -> int:

        result = await self.session.execute(
            select(func.count(Expense.id))
            .where(Expense.family_id == family_id)
        )

        return result.scalar_one()