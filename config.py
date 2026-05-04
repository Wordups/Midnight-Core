from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    ANTHROPIC_API_KEY: str = Field(..., min_length=1)
    SUPABASE_URL: str = Field(..., min_length=1)
    SUPABASE_ANON_KEY: str = Field(..., min_length=1)
    SUPABASE_SERVICE_ROLE_KEY: str = Field(..., min_length=1)
    ENVIRONMENT: Literal["dev", "prod"] = "dev"
    LOG_LEVEL: str = "INFO"

    @field_validator("ENVIRONMENT", mode="before")
    @classmethod
    def _normalize_environment(cls, v: str) -> str:
        aliases = {
            "development": "dev",
            "dev": "dev",
            "production": "prod",
            "prod": "prod",
        }
        normalized = aliases.get(str(v).strip().lower())
        if normalized is None:
            raise ValueError("ENVIRONMENT must be one of: dev, prod, development, production")
        return normalized

    @field_validator("LOG_LEVEL")
    @classmethod
    def _validate_log_level(cls, v: str) -> str:
        v = v.upper()
        if v not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError(f"LOG_LEVEL must be a standard logging level, got {v}")
        return v


settings = Settings()
