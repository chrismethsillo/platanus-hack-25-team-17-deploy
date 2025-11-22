"""Application settings using Pydantic Settings."""

import json

from pydantic import PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings.

    All settings can be overridden by environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Platanus API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: PostgresDsn
    DB_ECHO: bool = False

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Google Gemini API
    GEMINI_API_KEY: str | None = None

    # OpenAI API
    OPENAI_API_KEY: str | None = None

    # CORS
    BACKEND_CORS_ORIGINS: list[str] | str = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str] | str:
        """Parse CORS origins from string or list."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        if isinstance(v, str):
            return json.loads(v)
        if isinstance(v, list):
            return v
        raise ValueError(v)

    # API Documentation
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"
    OPENAPI_URL: str = "/openapi.json"

    # Logging
    LOG_LEVEL: str = "INFO"

    @property
    def database_url_async(self) -> str:
        """Get async database URL as string."""
        url = str(self.DATABASE_URL)
        # Convert postgresql:// to postgresql+asyncpg:// for async driver
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        # If already has a driver specified, return as is
        return url


settings = Settings()  # type: ignore
