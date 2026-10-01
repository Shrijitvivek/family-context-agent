"""Health endpoint. Never calls the AI model."""

from fastapi import APIRouter
from sqlalchemy import text

from app.api.dependencies import DbSession

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(session: DbSession) -> dict[str, str]:
    try:
        await session.execute(text("SELECT 1"))
        database = "ok"
    except Exception:
        database = "unavailable"
    return {"status": "ok", "database": database}
