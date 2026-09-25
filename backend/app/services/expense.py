# """Expense business service.

# TODO:
# - Validate and record expenses.
# - Query database-backed summaries for categories and date ranges.
# - Trigger any relevant dashboard refresh/event recording.
# """


from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.expense_repository import ExpenseRepository


class ExpenseService:
    """Business logic for expenses."""

    def __init__(self, session: AsyncSession):
        self.repository = ExpenseRepository(session)
        self.session = session

    async def create_expense(
        self,
        family_id: UUID,
        amount: Decimal,
        category: str,
        expense_date: date,
        member_id: UUID | None = None,
        merchant: str | None = None,
        description: str | None = None,
        source: str | None = None,
    ):

        if amount <= 0:
            raise ValueError("Expense amount must be greater than zero.")

        if not category.strip():
            raise ValueError("Expense category is required.")

        expense = await self.repository.create(
            family_id=family_id,
            amount=amount,
            category=category,
            expense_date=expense_date,
            member_id=member_id,
            merchant=merchant,
            description=description,
            source=source,
        )

        await self.session.commit()

        return expense

    async def get_expense(
        self,
        expense_id: UUID,
    ):

        return await self.repository.get_by_id(expense_id)

    async def get_family_expenses(
        self,
        family_id: UUID,
    ):

        return await self.repository.get_by_family(family_id)

    async def get_member_expenses(
        self,
        member_id: UUID,
    ):

        return await self.repository.get_by_member(member_id)

    async def update_expense(
        self,
        expense_id: UUID,
        **values,
    ):

        expense = await self.repository.update(
            expense_id,
            **values,
        )

        if expense is None:
            raise ValueError("Expense not found.")

        await self.session.commit()

        return expense

    async def delete_expense(
        self,
        expense_id: UUID,
    ):

        deleted = await self.repository.delete(expense_id)

        if not deleted:
            raise ValueError("Expense not found.")

        await self.session.commit()

        return True

    async def get_family_total(
        self,
        family_id: UUID,
    ):

        return await self.repository.get_total_for_family(family_id)

    async def get_family_count(
        self,
        family_id: UUID,
    ):

        return await self.repository.get_count_for_family(family_id)
