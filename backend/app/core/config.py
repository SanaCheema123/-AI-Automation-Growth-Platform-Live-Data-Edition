from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "AI Automation Growth Platform API"
    ENVIRONMENT: Literal["development", "test", "production"] = "development"
    API_PREFIX: str = "/api/v1"
    SECRET_KEY: str = "dev-only-change-me"
    TOKEN_ISSUER: str = "ai-automation-growth-platform"
    TOKEN_AUDIENCE: str = "ai-automation-growth-ui"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    DATABASE_URL: str = "sqlite:///./automation_dev.db"
    SUPABASE_DB_URL: str = ""
    AUTO_CREATE_TABLES: bool = True

    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    REQUEST_ID_HEADER: str = "X-Request-ID"

    # Live AI only. "auto" tries Gemini first, then Groq when both keys exist.
    AI_PROVIDER: Literal["auto", "gemini", "groq"] = "auto"
    AI_FALLBACK_TO_SECONDARY: bool = True
    AI_LOG_CONTENT: bool = False

    # Gemini API has a free usage tier subject to Google's current limits.
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_TIMEOUT_SECONDS: float = 30.0
    GEMINI_MAX_RETRIES: int = 2

    # Groq has a free plan subject to Groq's current limits.
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-20b"
    GROQ_TIMEOUT_SECONDS: float = 30.0
    GROQ_MAX_RETRIES: int = 2

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        value = (self.SUPABASE_DB_URL or self.DATABASE_URL).strip()
        if not value:
            raise RuntimeError("DATABASE_URL or SUPABASE_DB_URL must be configured")
        if value.startswith("postgres://"):
            value = "postgresql+psycopg://" + value[len("postgres://") :]
        elif value.startswith("postgresql://"):
            value = "postgresql+psycopg://" + value[len("postgresql://") :]
        return value

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def effective_ai_provider(self) -> str:
        if self.AI_PROVIDER == "gemini":
            return "gemini" if self.GEMINI_API_KEY else "unconfigured"
        if self.AI_PROVIDER == "groq":
            return "groq" if self.GROQ_API_KEY else "unconfigured"
        if self.GEMINI_API_KEY:
            return "gemini"
        if self.GROQ_API_KEY:
            return "groq"
        return "unconfigured"

    @property
    def ai_ready(self) -> bool:
        return self.effective_ai_provider in {"gemini", "groq"}

    def validate_runtime(self) -> None:
        # Missing AI keys do not stop the CRM/workflow application from starting.
        # AI endpoints return a clear 503 until a free-tier provider key is configured.
        if self.is_production:
            if self.SECRET_KEY == "dev-only-change-me" or len(self.SECRET_KEY) < 32:
                raise RuntimeError("Production SECRET_KEY must be a strong value of at least 32 characters")
            if self.database_url.startswith("sqlite"):
                raise RuntimeError("Production requires PostgreSQL/Supabase; SQLite is local/test only")
            if self.AUTO_CREATE_TABLES:
                raise RuntimeError("Set AUTO_CREATE_TABLES=false in production and apply SQL migrations explicitly")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
