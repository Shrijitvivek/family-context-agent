"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import (
    AIModelError,
    ConflictError,
    FamilyContextError,
    InvalidUploadError,
    NotFoundError,
    PersistenceError,
    ScopeViolationError,
    ToolInputValidationError,
)
from app.db.session import engine
from app.jobs.scheduler import start_scheduler, stop_scheduler

# Checked in order, so subclasses come before their base class.
_ERROR_STATUS: tuple[tuple[type[FamilyContextError], int], ...] = (
    (NotFoundError, status.HTTP_404_NOT_FOUND),
    (ScopeViolationError, status.HTTP_403_FORBIDDEN),
    (ConflictError, status.HTTP_409_CONFLICT),
    (ToolInputValidationError, status.HTTP_422_UNPROCESSABLE_ENTITY),
    (InvalidUploadError, status.HTTP_422_UNPROCESSABLE_ENTITY),
    (AIModelError, status.HTTP_503_SERVICE_UNAVAILABLE),
    (PersistenceError, status.HTTP_503_SERVICE_UNAVAILABLE),
)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    start_scheduler()
    try:
        yield
    finally:
        stop_scheduler()
        await engine.dispose()


app = FastAPI(
    title="Family Context Agent",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(FamilyContextError)
async def handle_domain_error(_: Request, exc: FamilyContextError) -> JSONResponse:
    status_code = next(
        (code for error_type, code in _ERROR_STATUS if isinstance(exc, error_type)),
        status.HTTP_400_BAD_REQUEST,
    )
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": exc.code, "message": str(exc), "details": exc.details}},
    )


app.include_router(api_router, prefix="/api/v1")
