"""Typed application configuration.

Values are read from real environment variables first, then from the root .env
file. Only database settings are defined so far.

TODO:
- Validate Nebius, upload, CORS, logging, and scheduler settings.
- Never hard-code or log secrets.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/core/config.py -> project root
ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/family_context"


@lru_cache
def get_settings() -> Settings:
    return Settings()
