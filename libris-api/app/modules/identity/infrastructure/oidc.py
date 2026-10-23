import asyncio
import os
from collections.abc import Mapping
from dataclasses import dataclass

import jwt
from jwt import InvalidTokenError, PyJWKClient
from jwt.exceptions import PyJWKClientConnectionError, PyJWKClientError

from app.modules.identity.domain.exceptions import AuthenticationError, ProviderUnavailable


def _positive_number(name: str, default: str) -> float:
    raw_value = os.getenv(name, default)
    try:
        value = float(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} deve ser numerico.") from exc
    if value <= 0:
        raise ValueError(f"{name} deve ser maior que zero.")
    return value


@dataclass(frozen=True)
class OidcSettings:
    issuer: str
    audience: str
    algorithms: tuple[str, ...]
    jwks_cache_ttl: int
    clock_skew_seconds: float
    http_timeout_seconds: float
    role_source: str
    role_client: str
    human_client: str
    access_token_claim: str
    access_token_value: str

    @classmethod
    def from_environment(cls) -> "OidcSettings":
        issuer = os.getenv(
            "OIDC_ISSUER_URL", "http://keycloak.localhost:8081/realms/libris"
        ).rstrip("/")
        algorithms = tuple(
            algorithm.strip()
            for algorithm in os.getenv("OIDC_ALGORITHMS", "RS256").split(",")
            if algorithm.strip()
        )
        role_source = os.getenv("OIDC_ROLE_SOURCE", "client")
        if not issuer.startswith(("http://", "https://")):
            raise ValueError("OIDC_ISSUER_URL deve usar HTTP ou HTTPS.")
        if not algorithms:
            raise ValueError("OIDC_ALGORITHMS deve conter ao menos um algoritmo.")
        if role_source not in {"client", "realm"}:
            raise ValueError("OIDC_ROLE_SOURCE deve ser 'client' ou 'realm'.")

        return cls(
            issuer=issuer,
            audience=os.getenv("OIDC_AUDIENCE", "libris-api"),
            algorithms=algorithms,
            jwks_cache_ttl=int(_positive_number("OIDC_JWKS_CACHE_TTL", "300")),
            clock_skew_seconds=_positive_number("OIDC_CLOCK_SKEW_SECONDS", "30"),
            http_timeout_seconds=_positive_number("OIDC_HTTP_TIMEOUT_SECONDS", "5"),
            role_source=role_source,
            role_client=os.getenv("OIDC_ROLE_CLIENT", "libris-api"),
            human_client=os.getenv("OIDC_HUMAN_CLIENT_ID", "libris-web"),
            access_token_claim=os.getenv("OIDC_ACCESS_TOKEN_CLAIM", "typ"),
            access_token_value=os.getenv("OIDC_ACCESS_TOKEN_VALUE", "Bearer"),
        )


class OidcTokenValidator:
    def __init__(self, settings: OidcSettings) -> None:
        self.settings = settings
        self.jwks_client = PyJWKClient(
            f"{settings.issuer}/protocol/openid-connect/certs",
            cache_keys=True,
            lifespan=settings.jwks_cache_ttl,
            timeout=settings.http_timeout_seconds,
        )

    def _validate(self, token: str) -> Mapping[str, object]:
        try:
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=list(self.settings.algorithms),
                audience=self.settings.audience,
                issuer=self.settings.issuer,
                leeway=self.settings.clock_skew_seconds,
                options={"require": ["exp", "iss", "sub", "aud"]},
            )
        except PyJWKClientConnectionError as exc:
            raise ProviderUnavailable() from exc
        except (InvalidTokenError, PyJWKClientError) as exc:
            raise AuthenticationError() from exc

        if claims.get(self.settings.access_token_claim) != self.settings.access_token_value:
            raise AuthenticationError()
        return claims

    async def validate(self, token: str) -> Mapping[str, object]:
        return await asyncio.to_thread(self._validate, token)
