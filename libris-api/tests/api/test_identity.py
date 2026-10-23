import asyncio
import time
from collections.abc import Mapping

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.modules.identity.application.service import IdentityService
from app.modules.identity.domain.exceptions import AuthenticationError
from app.modules.identity.infrastructure.oidc import OidcSettings, OidcTokenValidator


class StubValidator:
    def __init__(self, claims: Mapping[str, object] | None = None) -> None:
        self.claims = claims

    async def validate(self, token: str) -> Mapping[str, object]:
        if token != "valid-token" or self.claims is None:
            raise AuthenticationError()
        return self.claims


class NullSecuritySink:
    def emit(self, event: object) -> None:
        pass


class StubSigningKeyClient:
    def __init__(self, key: object) -> None:
        self.key = key

    def get_signing_key_from_jwt(self, token: str):
        return type("SigningKey", (), {"key": self.key})()


async def request_identity(token: str | None = None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get("/api/v1/identity/me", headers=headers)


def install_service(claims: Mapping[str, object] | None = None) -> None:
    app.state.identity_service = IdentityService(
        validator=StubValidator(claims),
        role_source="client",
        role_client="libris-api",
        human_client="libris-web",
        observer=NullSecuritySink(),
    )


def test_identity_service_is_initialized() -> None:
    assert isinstance(app.state.identity_service, IdentityService)


def test_identity_requires_a_bearer_token() -> None:
    install_service()
    response = asyncio.run(request_identity())

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_identity_rejects_an_invalid_token_instead_of_returning_500() -> None:
    install_service()
    response = asyncio.run(request_identity("invalid-token"))

    assert response.status_code == 401


def test_identity_returns_actor_roles_and_permissions() -> None:
    install_service(
        {
            "azp": "libris-web",
            "iss": "http://keycloak.localhost:8081/realms/libris",
            "sub": "user-123",
            "resource_access": {
                "libris-api": {"roles": ["libris-reader", "libris-admin"]}
            },
        }
    )
    response = asyncio.run(request_identity("valid-token"))

    assert response.status_code == 200
    payload = response.json()
    assert payload["actor_id"].startswith("oidc:sha256:")
    assert payload["roles"] == ["libris-admin", "libris-reader"]
    assert payload["permissions"] == ["bibliographic:read", "system:admin"]


def test_oidc_validator_verifies_a_signed_access_token() -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    settings = OidcSettings.from_environment()
    validator = OidcTokenValidator(settings)
    validator.jwks_client = StubSigningKeyClient(private_key.public_key())
    claims = {
        "aud": settings.audience,
        "azp": settings.human_client,
        "exp": int(time.time()) + 60,
        "iss": settings.issuer,
        "sub": "user-123",
        settings.access_token_claim: settings.access_token_value,
    }
    token = jwt.encode(claims, private_key, algorithm="RS256")

    assert asyncio.run(validator.validate(token)) == claims


def test_oidc_validator_rejects_an_id_token() -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    settings = OidcSettings.from_environment()
    validator = OidcTokenValidator(settings)
    validator.jwks_client = StubSigningKeyClient(private_key.public_key())
    token = jwt.encode(
        {
            "aud": settings.audience,
            "exp": int(time.time()) + 60,
            "iss": settings.issuer,
            "sub": "user-123",
            settings.access_token_claim: "ID",
        },
        private_key,
        algorithm="RS256",
    )

    with pytest.raises(AuthenticationError):
        asyncio.run(validator.validate(token))
