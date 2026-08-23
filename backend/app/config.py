"""Application configuration.

Everything comes from environment variables. No credential is ever written
into source, migrations or documentation (D034).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(REPO_ROOT / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

    # --- database ---
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/ishara_ai"

    # --- auth ---
    jwt_secret: str = "change_me"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    refresh_token_days: int = 7

    # --- seed ---
    seed_admin_email: str = "admin@isharaai.local"
    seed_admin_password: str = "change_me"

    # --- speech ---
    kokoro_voice: str = ""
    kokoro_lang: str = "h"

    # --- doctor STT (P1, optional — the demo runs without it) ---
    groq_api_key: str = ""
    groq_stt_model: str = "whisper-large-v3-turbo"
    local_stt_model: str = "small"
    local_stt_compute: str = "int8"

    # --- paths ---
    @property
    def repo_root(self) -> Path:
        return REPO_ROOT

    @property
    def assets_dir(self) -> Path:
        return REPO_ROOT / "assets"

    @property
    def audio_dir(self) -> Path:
        return REPO_ROOT / "assets" / "audio"

    @property
    def video_dir(self) -> Path:
        return REPO_ROOT / "assets" / "psl-videos"

    @property
    def snapshot_dir(self) -> Path:
        return REPO_ROOT / "data"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    # SQLAlchemy needs the driver in the URL; .env carries the plain libpq form.
    if settings.database_url.startswith("postgresql://"):
        settings.database_url = settings.database_url.replace(
            "postgresql://", "postgresql+psycopg2://", 1
        )
    return settings


settings = get_settings()
