import ipaddress
import re
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
    cors_origins: list[str] = Field(default_factory=list)

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
    oidc_human_client_id: str = "libris-web"
    oidc_access_token_claim: str = "typ"
    oidc_access_token_value: str = "Bearer"

    @model_validator(mode="after")
    def validate_cors(self) -> "Settings":
        for origin in self.cors_origins:
            parts = urlsplit(origin)
            port = parts.port
            host = parts.hostname or ""
            try:
                ipaddress.ip_address(host)
                valid_host = True
            except ValueError:
                # DNS labels are ASCII, without browser URL-parser normalization.
                valid_host = bool(re.fullmatch(
                    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
                    r"(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)*", host
                )) and len(host) <= 253
            if (
                parts.scheme not in {"http", "https"}
                or not valid_host
                or parts.username is not None
                or parts.password is not None
                or parts.path or parts.query or parts.fragment
                or any(char in origin for char in "\\?#")
                or any(char.isspace() or ord(char) < 32 for char in origin)
                or parts.netloc.endswith(":")
                or (port is not None and not 1 <= port <= 65535)
                or origin != f"{parts.scheme}://{parts.netloc}"
            ):
                raise ValueError("CORS_ORIGINS exige origens HTTP(S) exatas, sem wildcard.")
            if parts.scheme == "http" and (
                self.app_env == "production"
                or not (host in {"localhost", "127.0.0.1", "::1"} or host.endswith(".localhost"))
            ):
                raise ValueError("CORS HTTP somente para loopback/local em desenvolvimento.")
        if len(self.cors_origins) != len(set(self.cors_origins)):
            raise ValueError("CORS_ORIGINS não aceita duplicatas.")
        return self

    @property
    def allowed_oidc_algorithms(self) -> list[str]:
        return [value.strip() for value in self.oidc_algorithms.split(",")]

    @model_validator(mode="after")
    def validate_oidc(self) -> "Settings":
        parts = urlsplit(self.oidc_issuer_url)
        if (
            parts.scheme not in {"http", "https"}
            or not parts.hostname
            or (parts.port is not None and not 1 <= parts.port <= 65535)
            or parts.netloc.endswith(":")
            or parts.username is not None
            or parts.password is not None
            or any(char.isspace() or ord(char) < 32 for char in self.oidc_issuer_url)
            or "\\" in self.oidc_issuer_url
            or parts.query
            or parts.fragment
        ):
            raise ValueError("OIDC_ISSUER_URL deve ser HTTP(S) absoluta sem credenciais.")
        if self.app_env == "production" and parts.scheme != "https":
            raise ValueError("OIDC exige HTTPS em produção.")
        supported = {"RS256", "RS384", "RS512", "ES256", "ES384", "ES512", "EdDSA"}
        if not set(self.allowed_oidc_algorithms) <= supported:
            raise ValueError("OIDC_ALGORITHMS exige algoritmos assimétricos permitidos.")
        for value in (
            self.oidc_audience,
            self.oidc_role_client,
            self.oidc_human_client_id,
            self.oidc_access_token_claim,
            self.oidc_access_token_value,
        ):
            if not value.strip():
                raise ValueError("Configuração OIDC obrigatória vazia.")
        return self
