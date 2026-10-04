"""Version 1 API router."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    chat,
    commitments,
    demo,
    documents,
    expenses,
    families,
    health,
    members,
    priorities,
    timeline,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(families.router)
api_router.include_router(members.router)
api_router.include_router(commitments.router)
api_router.include_router(expenses.router)
api_router.include_router(priorities.router)
api_router.include_router(timeline.router)
api_router.include_router(chat.router)
api_router.include_router(documents.router)
api_router.include_router(demo.router)
