
"""FastAPI application entry point.

TODO:
- Create the FastAPI application and configure metadata.
- Register the versioned API router and CORS middleware.
- Start and stop database and scheduler resources in lifespan hooks.
- Add clean exception handlers without placing business logic here.
"""
"""FastAPI application entry point."""

from fastapi import FastAPI

from app.api.v1.endpoints.chat import router as chat_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Family Context Agent",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    chat_router,
    prefix="/api/v1",
    tags=["Chat"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
