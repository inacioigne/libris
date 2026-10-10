import asyncio
import json
import time
from collections.abc import Iterator
from dataclasses import FrozenInstanceError

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import Depends
from fastapi.testclient import TestClient
from pydantic import ValidationError

from libris.core.config import Settings
from libris.main import create_app
from libris.modules.identity.api.dependencies import (
    get_current_actor,
    require_permissions,
)
from libris.modules.identity.application.service import IdentityService, authorize
from libris.modules.identity.domain.exceptions import (
    AuthenticationError,
    PermissionDenied,
)
from libris.modules.identity.domain.models import AuthenticatedActor, actor_identifier
from libris.modules.identity.domain.permissions import Permission as P
from libris.modules.identity.infrastructure.oidc import OIDCValidator
from libris.modules.identity.infrastructure.role_mapper import (
    extract_roles,
    map_permissions,
)


class Provider:
    def __init__(self) -> None:
        self.settings = Settings(_env_file=None, oidc_enabled=True, oidc_clock_skew_seconds=0)
        self.private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.keys = [self.jwk(self.private, "one")]
        self.calls: list[str] = []
        self.now = 1000.0
        self.status = 200
        self.invalid_keys = False
        self.timeout = False
        self.discovery_issuer = self.settings.oidc_issuer_url
        self.client = httpx.AsyncClient(transport=httpx.MockTransport(self.handle))
        self.validator = OIDCValidator(self.settings, self.client, lambda: self.now)

    @staticmethod
    def jwk(private: rsa.RSAPrivateKey, kid: str) -> dict[str, object]:
        value: dict[str, object] = json.loads(
            jwt.algorithms.RSAAlgorithm.to_jwk(private.public_key())
        )
        return {**value, "kid": kid, "use": "sig", "alg": "RS256"}

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.calls.append(request.url.path)
        if self.timeout:
            raise httpx.ReadTimeout("timeout")
        if request.url.path.endswith("openid-configuration"):
            document: object = {
                "issuer": self.discovery_issuer,
                "jwks_uri": "http://provider/keys",
            }
        else:
            document = {"keys": "invalid" if self.invalid_keys else self.keys}
        return httpx.Response(self.status, json=document)

    def token(
        self,
        changes: dict[str, object] | None = None,
        *,
        omit: str | None = None,
        private: rsa.RSAPrivateKey | None = None,
        kid: str | None = "one",
        headers: dict[str, object] | None = None,
    ) -> str:
        now = int(time.time())
        claims: dict[str, object] = {
            "iss": self.settings.oidc_issuer_url,
            "sub": "subject",
            "aud": "libris-api",
            "exp": now + 600,
            "iat": now - 1,
            "typ": "Bearer",
            "resource_access": {"libris-api": {"roles": ["libris-cataloger"]}},
        }
        claims.update(changes or {})
        if omit:
            claims.pop(omit)
        return jwt.encode(
            claims,
            private or self.private,
            algorithm="RS256",
            headers={**({"kid": kid} if kid is not None else {}), **(headers or {})},
        )


@pytest.fixture
def provider() -> Iterator[Provider]:
    value = Provider()
    yield value
    asyncio.run(value.client.aclose())


def test_valid_token_and_actor(provider: Provider) -> None:
    service = IdentityService(provider.validator, "client", "libris-api")
    actor = asyncio.run(service.authenticate(provider.token()))
    assert actor.actor_id == actor_identifier(provider.settings.oidc_issuer_url, "subject")
    assert P.BIBLIOGRAPHIC_CREATE in actor.permissions
    assert P.SYSTEM_ADMIN not in actor.permissions
    with pytest.raises(FrozenInstanceError):
        actor.actor_id = "changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    "changes,omit",
    [
        ({"exp": 1}, None),
        ({"iss": "https://wrong"}, None),
        ({"aud": "libris-web"}, None),
        ({"sub": ""}, None),
        ({"sub": " "}, None),
        ({}, "sub"),
        ({}, "exp"),
        ({"nbf": time.time() + 600}, None),
        ({"iat": time.time() + 600}, None),
        ({"typ": "ID"}, None),
        ({}, "typ"),
        ({"exp": "9999999999"}, None),
        ({"exp": True}, None),
        ({"exp": float("nan")}, None),
    ],
)
def test_invalid_claims(provider: Provider, changes: dict[str, object], omit: str | None) -> None:
    with pytest.raises(AuthenticationError):
        asyncio.run(provider.validator.validate(provider.token(changes, omit=omit)))


def test_signature_and_manipulated_roles(provider: Provider) -> None:
    token = provider.token(
        {"resource_access": {"libris-api": {"roles": ["libris-admin"]}}},
        private=provider.other,
    )
    with pytest.raises(AuthenticationError):
        asyncio.run(provider.validator.validate(token))


@pytest.mark.parametrize("token", ["broken", "a.b.c", "", "x" * 16385])
def test_malformed(provider: Provider, token: str) -> None:
    with pytest.raises(AuthenticationError):
        asyncio.run(provider.validator.validate(token))
    assert provider.calls == []


@pytest.mark.parametrize("algorithm", ["none", "HS256"])
def test_disallowed_algorithm(provider: Provider, algorithm: str) -> None:
    token = jwt.encode(
        {"sub": "s"},
        "x" * 32 if algorithm == "HS256" else None,
        algorithm=algorithm,
        headers={"kid": "one"},
    )
    with pytest.raises(AuthenticationError):
        asyncio.run(provider.validator.validate(token))
    assert not provider.calls


def test_cache_expiration_rotation_and_refresh_limit(provider: Provider) -> None:
    async def scenario() -> None:
        token = provider.token(headers={"jku": "http://attacker/keys"})
        await provider.validator.validate(token)
        await provider.validator.validate(token)
        assert len(provider.calls) == 2
        for _ in range(20):
            with pytest.raises(AuthenticationError):
                await provider.validator.validate(provider.token(kid="unknown"))
        assert len(provider.calls) == 2
        provider.now += 11
        provider.keys.append(provider.jwk(provider.other, "two"))
        await provider.validator.validate(provider.token(private=provider.other, kid="two"))
        assert len(provider.calls) == 3
        provider.now += 301
        await provider.validator.validate(token)
        assert len(provider.calls) == 4

    asyncio.run(scenario())


@pytest.mark.parametrize("failure", ["status", "timeout", "invalid_keys", "issuer"])
def test_provider_failure_and_backoff(provider: Provider, failure: str) -> None:
    if failure == "status":
        provider.status = 503
    elif failure == "issuer":
        provider.discovery_issuer = "http://wrong"
    else:
        setattr(provider, failure, True)

    async def scenario() -> None:
        for _ in range(10):
            with pytest.raises(AuthenticationError):
                await provider.validator.validate(provider.token())
        assert len(provider.calls) <= 2

    asyncio.run(scenario())


def test_no_stale_keys_after_expiration(provider: Provider) -> None:
    async def scenario() -> None:
        await provider.validator.validate(provider.token())
        provider.now += 301
        provider.status = 503
        with pytest.raises(AuthenticationError):
            await provider.validator.validate(provider.token())

    asyncio.run(scenario())


def test_unknown_key_after_refresh(provider: Provider) -> None:
    with pytest.raises(AuthenticationError):
        asyncio.run(provider.validator.validate(provider.token(kid="missing")))
    assert len(provider.calls) == 2


@pytest.mark.parametrize(
    "roles,expected",
    [
        (frozenset(), frozenset()),
        (frozenset({"unknown"}), frozenset()),
        (
            frozenset({"libris-reader"}),
            frozenset({P.BIBLIOGRAPHIC_READ, P.AUTHORITY_READ}),
        ),
        (frozenset({"libris-admin"}), frozenset(P)),
    ],
)
def test_role_mapping(roles: frozenset[str], expected: frozenset[P]) -> None:
    assert map_permissions(roles) == expected


def test_union_and_trusted_role_source() -> None:
    assert map_permissions(frozenset({"libris-reader", "libris-cataloger", "unknown"})) == (
        map_permissions(frozenset({"libris-cataloger"}))
    )
    claims: dict[str, object] = {
        "realm_access": {"roles": ["libris-admin"]},
        "resource_access": {"other-client": {"roles": ["libris-admin"]}},
    }
    assert extract_roles(claims, "client", "libris-api") == frozenset()
    assert extract_roles(claims, "realm", "libris-api") == frozenset({"libris-admin"})
    assert extract_roles({"realm_access": {"roles": "libris-admin"}}, "realm", "x") == frozenset()
    assert extract_roles({"realm_access": {"roles": [1]}}, "realm", "x") == frozenset()


def test_identifier_stability(provider: Provider) -> None:
    assert actor_identifier("issuer", "subject") == actor_identifier("issuer", "subject")
    assert actor_identifier("issuer", "subject") != actor_identifier("other", "subject")
    assert actor_identifier("ab", "c") != actor_identifier("a", "bc")

    async def scenario() -> None:
        first = IdentityService(provider.validator, "client", "libris-api")
        second = IdentityService(provider.validator, "client", "libris-api")
        a = await first.authenticate(provider.token({"name": "A", "email": "a@example.invalid"}))
        b = await second.authenticate(provider.token({"name": "B", "email": "b@example.invalid"}))
        assert a.actor_id == b.actor_id

    asyncio.run(scenario())


def test_fastapi_authentication_authorization_and_override(provider: Provider) -> None:
    app = create_app(provider.settings)

    @app.get("/test-protected")
    def protected(
        actor: AuthenticatedActor = Depends(require_permissions(P.BIBLIOGRAPHIC_CREATE)),
    ) -> str:
        return actor.actor_id

    @app.get("/test-admin")
    def admin(
        actor: AuthenticatedActor = Depends(require_permissions(P.SYSTEM_ADMIN)),
    ) -> str:
        return actor.actor_id

    with TestClient(app) as client:
        app.state.identity_service = IdentityService(provider.validator, "client", "libris-api")
        for headers in (
            {},
            {"Authorization": "Basic abc"},
            {"Authorization": "Bearer invalid"},
        ):
            response = client.get("/api/v1/identity/me", headers=headers)
            assert response.status_code == 401
            assert response.headers["www-authenticate"] == "Bearer"
        headers = {"Authorization": "Bearer " + provider.token()}
        response = client.get("/api/v1/identity/me", headers=headers)
        assert response.status_code == 200
        assert set(response.json()) == {"actor_id", "roles", "permissions"}
        assert client.get("/test-protected", headers=headers).status_code == 200
        assert client.get("/test-admin", headers=headers).status_code == 403
        no_roles = {"Authorization": "Bearer " + provider.token({"resource_access": {}})}
        assert client.get("/test-protected", headers=no_roles).status_code == 403
        actor = AuthenticatedActor("test", "issuer", "subject", frozenset(), frozenset(P))
        app.dependency_overrides[get_current_actor] = lambda: actor
        assert client.get("/test-admin").status_code == 200
        assert client.get("/api/v1/identity/me").json()["actor_id"] == "test"
        authorize(actor, (P.SYSTEM_ADMIN,))
        with pytest.raises(PermissionDenied):
            authorize(
                AuthenticatedActor("t", "i", "s", frozenset(), frozenset()),
                (P.SYSTEM_ADMIN,),
            )


def test_disabled_never_bypasses_authentication() -> None:
    with TestClient(create_app(Settings(_env_file=None, oidc_enabled=False))) as client:
        assert (
            client.get("/api/v1/identity/me", headers={"Authorization": "Bearer abc"}).status_code
            == 401
        )
        assert client.get("/health").status_code == 200


@pytest.mark.parametrize(
    "config",
    [
        {"oidc_algorithms": "none"},
        {"oidc_algorithms": "HS256"},
        {"oidc_algorithms": ""},
        {"oidc_jwks_cache_ttl": 0},
        {"oidc_issuer_url": "http://user:pass@host"},
        {
            "oidc_enabled": True,
            "app_env": "production",
            "oidc_issuer_url": "http://host",
        },
    ],
)
def test_settings_fail_closed(config: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **config)


def test_concurrent_initial_requests_share_refresh(provider: Provider) -> None:
    async def scenario() -> None:
        await asyncio.gather(*(provider.validator.validate(provider.token()) for _ in range(10)))
        assert len(provider.calls) == 2

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "mutation", ["missing-kid", "encryption", "wrong-alg", "bad-key", "duplicate"]
)
def test_incompatible_keys(provider: Provider, mutation: str) -> None:
    token = provider.token()
    if mutation == "missing-kid":
        token = provider.token(kid=None)
    elif mutation == "encryption":
        provider.keys[0]["use"] = "enc"
    elif mutation == "wrong-alg":
        provider.keys[0]["alg"] = "RS512"
    elif mutation == "bad-key":
        provider.keys[0]["n"] = ""
    else:
        provider.keys.append(dict(provider.keys[0]))
    with pytest.raises(AuthenticationError):
        asyncio.run(provider.validator.validate(token))


def test_expiration_infinity(provider: Provider) -> None:
    with pytest.raises(AuthenticationError):
        asyncio.run(provider.validator.validate(provider.token({"exp": float("inf")})))


def test_bearer_cors_preflight() -> None:
    with TestClient(create_app(Settings(_env_file=None))) as client:
        response = client.options(
            "/api/v1/identity/me",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization",
            },
        )
        assert response.status_code == 200
