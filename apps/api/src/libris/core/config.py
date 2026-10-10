from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, HttpUrl, PostgresDsn, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../../.env", extra="ignore")

    app_env: Literal["development", "test", "production"] = "development"
    database_url: PostgresDsn = Field(
        default=PostgresDsn(
            "postgresql+asyncpg://libris:change-me-local-only@localhost:5432/libris"
        )
    )
    elasticsearch_url: HttpUrl = Field(default=HttpUrl("http://localhost:9200"))
    resource_base_uri: HttpUrl = Field(default=HttpUrl("http://localhost:8000/resources"))
    rdf_max_document_bytes: int = Field(default=1_048_576, gt=0, le=10_485_760)
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    oidc_enabled: bool = False
    oidc_issuer_url: str = "http://localhost:8081/realms/libris"
    oidc_audience: str = "libris-api"
    oidc_algorithms: str = "RS256"
    oidc_jwks_cache_ttl: int = Field(default=300, gt=0)
    oidc_jwks_refresh_interval: int = Field(default=10, gt=0)
    oidc_clock_skew_seconds: int = Field(default=30, ge=0, le=300)
    oidc_http_timeout_seconds: float = Field(default=5, gt=0, le=60)
    oidc_role_source: Literal["client", "realm"] = "client"
    oidc_role_client: str = "libris-api"
    oidc_access_token_claim: str = "typ"
    oidc_access_token_value: str = "Bearer"

    @property
    def allowed_oidc_algorithms(self) -> list[str]:
        return [value.strip() for value in self.oidc_algorithms.split(",")]

    @model_validator(mode="after")
    def validate_oidc(self) -> "Settings":
        parts = urlsplit(self.oidc_issuer_url)
        if (
            parts.scheme not in {"http", "https"}
            or not parts.netloc
            or parts.username
            or parts.password
            or parts.query
            or parts.fragment
        ):
            raise ValueError("OIDC_ISSUER_URL deve ser HTTP(S) absoluta sem credenciais.")
        if self.oidc_enabled and self.app_env == "production" and parts.scheme != "https":
            raise ValueError("OIDC exige HTTPS em produção.")
        supported = {"RS256", "RS384", "RS512", "ES256", "ES384", "ES512", "EdDSA"}
        if not set(self.allowed_oidc_algorithms) <= supported:
            raise ValueError("OIDC_ALGORITHMS exige algoritmos assimétricos permitidos.")
        for value in (
            self.oidc_audience,
            self.oidc_role_client,
            self.oidc_access_token_claim,
            self.oidc_access_token_value,
        ):
            if not value.strip():
                raise ValueError("Configuração OIDC obrigatória vazia.")
        return self
