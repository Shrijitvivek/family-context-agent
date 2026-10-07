"""Typed application configuration.

Values are read from real environment variables first, then from the root .env
file. Secrets such as the Nebius API key must never be hard-coded or logged.
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

    cors_origins: str = "http://localhost:5173"
    family_timezone: str = "Asia/Kolkata"
    demo_family_name: str = "Nair Family"

    nebius_api_key: str = ""
    nebius_base_url: str = "https://api.studio.nebius.ai/v1/"
    nvidia_model_name: str = ""
    vision_model_name: str = "Qwen/Qwen2.5-VL-72B-Instruct"
    model_timeout_seconds: float = 60.0

    upload_dir: str = "storage/uploads"
    max_upload_size_mb: int = 10
    allowed_upload_types: str = "application/pdf,image/jpeg,image/png"

    scheduler_enabled: bool = True
    deadline_check_interval_minutes: int = 60

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def allowed_upload_type_set(self) -> frozenset[str]:
        return frozenset(t.strip() for t in self.allowed_upload_types.split(",") if t.strip())

    @property
    def demo_scenario_dir(self) -> Path:
        return ROOT_DIR / "synthetic_data" / "scenarios"

    @property
    def upload_path(self) -> Path:
        path = Path(self.upload_dir)
        return path if path.is_absolute() else ROOT_DIR / path


@lru_cache
def get_settings() -> Settings:
    return Settings()
