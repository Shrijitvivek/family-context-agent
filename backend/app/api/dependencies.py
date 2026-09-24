"""
FastAPI dependencies for database-backed services and tools.
"""

from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.ai_model import AIModelClient
from app.db.session import get_db
from app.repositories.commitment import CommitmentRepository
from app.repositories.expense import ExpenseRepository
from app.services.commitment import CommitmentService
from app.services.expense import ExpenseService
from app.tools.registry import ToolRegistry


async def get_tool_registry(
    db: AsyncSession = Depends(get_db),
) -> ToolRegistry:

    expense_repository = ExpenseRepository(
        db
    )

    commitment_repository = CommitmentRepository(
        db
    )

    expense_service = ExpenseService(
        expense_repository
    )

    commitment_service = CommitmentService(
        commitment_repository
    )

    return ToolRegistry(
        expense_service=expense_service,
        commitment_service=commitment_service,
    )


def get_ai_client() -> AIModelClient:

    return AIModelClient()
