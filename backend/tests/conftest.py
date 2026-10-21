
"""Shared pytest fixtures."""

import pytest_asyncio

from app.db.session import engine as app_engine


@pytest_asyncio.fixture(scope="session", loop_scope="session", autouse=True)
async def dispose_test_engine():
    yield
    await app_engine.dispose()
