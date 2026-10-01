"""Shared FastAPI dependencies.

TODO:
- Provide database sessions and authenticated/demo family context.
- Resolve request IDs and other request-scoped resources.
- Keep dependency functions thin and free of business rules.
"""
"""Shared FastAPI dependencies."""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.orchestrator import FamilyContextAgent
from app.clients.ai_model import AIModelClient
from app.repositories.commitment import CommitmentRepository
from app.repositories.expense import ExpenseRepository
from app.repositories.family import FamilyRepository
from app.services.commitment import CommitmentService
from app.services.expense import ExpenseService
from app.services.family import FamilyService
from app.tools.registry import ToolRegistry
from app.db.session import get_db


async def get_family_service(
    session: AsyncSession = Depends(get_db),
) -> FamilyService:
    return FamilyService(FamilyRepository(session))


FamilyServiceDep = Annotated[FamilyService, Depends(get_family_service)]


async def get_expense_service(
    session: AsyncSession,
) -> ExpenseService:
    repository = ExpenseRepository(session)
    return ExpenseService(repository)


async def get_commitment_service(
    session: AsyncSession,
) -> CommitmentService:
    repository = CommitmentRepository(session)
    return CommitmentService(repository)


async def get_tool_registry(
    session: AsyncSession,
) -> ToolRegistry:
    expense_service = ExpenseService(
        ExpenseRepository(session)
    )
    commitment_service = CommitmentService(
        CommitmentRepository(session)
    )

    return ToolRegistry(
        expense_service=expense_service,
        commitment_service=commitment_service,
    )


async def get_family_context_agent(
    session: AsyncSession,
) -> FamilyContextAgent:
    ai_client = AIModelClient()

    tool_registry = ToolRegistry(
        expense_service=ExpenseService(
            ExpenseRepository(session)
        ),
        commitment_service=CommitmentService(
            CommitmentRepository(session)
        ),
    )

    return FamilyContextAgent(
        ai_client=ai_client,
        tool_registry=tool_registry,
    )
