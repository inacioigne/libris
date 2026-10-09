from typing import Literal

from pydantic import Field, HttpUrl, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../../.env", extra="ignore")

    app_env: Literal["development", "test", "production"] = "development"
    database_url: PostgresDsn = Field(
        default=PostgresDsn("postgresql+asyncpg://libris:change-me-local-only@localhost:5432/libris")
    )
    elasticsearch_url: HttpUrl = Field(default=HttpUrl("http://localhost:9200"))
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
