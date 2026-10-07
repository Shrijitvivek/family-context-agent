"""FastAPI application entry point."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.exceptions import FamilyContextError

from contextlib import asynccontextmanager

from app.jobs.scheduler import start_scheduler, stop_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()

    yield

    stop_scheduler()

app = FastAPI(
    title="Family Context Agent",
    version="1.0.0",
    lifespan=lifespan,
)


# Exception handlers for the Family Context Agent API.
@app.exception_handler(FamilyContextError)
async def family_context_error_handler(
    request: Request,
    exc: FamilyContextError,
) -> JSONResponse:
    status_code = 409 if exc.code.startswith(
        ("conflict", "duplicate", "dependency_")
    ) else 400

    return JSONResponse(
        status_code=status_code,
        content={
            "code": exc.code,
            "message": str(exc),
            "details": exc.details,
        },
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    api_router,
    prefix="/api/v1",
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}