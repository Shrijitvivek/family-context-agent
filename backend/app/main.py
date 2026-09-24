from fastapi import FastAPI

from app.api.v1.endpoints.chat import router as chat_router


app = FastAPI(
    title="Family Context Agent",
    version="1.0.0",
)


app.include_router(
    chat_router,
    prefix="/api/v1",
)


@app.get("/health")
async def health():

    return {
        "status": "ok",
        "service": "family-context-agent",
    }