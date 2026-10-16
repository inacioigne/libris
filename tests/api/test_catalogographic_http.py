"""M05.01 composition and dependencies; no operational catalog endpoints exist yet."""

import asyncio
import json
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
from fastapi import APIRouter, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient
from pydantic import BaseModel, ValidationError

from libris import main
from libris.api.problems import classify, handle_request_validation
from libris.core.config import Settings
from libris.core.correlation import request_id_context
from libris.infrastructure.database import Database
from libris.modules.bibliographic.api.dependencies import get_session_factory
from libris.modules.bibliographic.api.router import router
from libris.modules.bibliographic.api.schemas import (
    AgentCreate,
    InstanceCreate,
    ItemCreate,
    SubjectCreate,
    WorkCreate,
)
from libris.modules.identity.api.dependencies import (
    get_authorization_guard,
    get_current_actor,
    get_execution_context,
)
from libris.modules.identity.domain.authorization import Operation as O
from libris.modules.identity.domain.authorization import ResourceContext, ResourceKind
from libris.modules.identity.domain.exceptions import PermissionDenied
from libris.modules.identity.domain.models import AuthenticatedActor, actor_identifier
from libris.modules.identity.domain.permissions import Permission as P


def actor(*permissions: P) -> AuthenticatedActor:
    issuer, subject = "https://issuer.example.invalid", "synthetic-test-actor"
    return AuthenticatedActor(
        actor_identifier(issuer, subject), issuer, subject, frozenset(), frozenset(permissions)
    )


def test_catalog_composition_point_is_included(monkeypatch: pytest.MonkeyPatch) -> None:
    # Replace only the composition point to prove create_app includes it. This
    # executable probe belongs exclusively to the test, never the product router.
    probe = APIRouter(prefix=router.prefix, tags=router.tags)

    @probe.get("/composition-probe")
    def composed() -> dict[str, bool]:
        return {"composed": True}

    monkeypatch.setattr(main, "catalog_router", probe)
    app = main.create_app(Settings(_env_file=None, app_env="test"))
    with TestClient(app) as client:
        assert client.get("/api/v1/catalog/composition-probe").json() == {"composed": True}
    assert router.prefix == "/api/v1/catalog"
    assert router.tags == ["catalog"]
    assert router.routes == []


def test_lifespan_factory_and_legacy_routes_without_connections() -> None:
    app = main.create_app(Settings(_env_file=None, app_env="test", oidc_enabled=False))
    # Factory access and liveness must not open a database connection.
    with (
        patch("sqlalchemy.ext.asyncio.AsyncEngine.connect", side_effect=AssertionError),
        patch(
            "libris.infrastructure.database.Database.close",
            autospec=True, side_effect=Database.close,
        ) as close,
    ):
        with TestClient(app) as client:
            request = Request({"type": "http", "app": app})
            factory = get_session_factory(request)
            assert factory is app.state.database.sessions
            first, second = factory(), factory()
            assert first is not second
            assert not first.in_transaction() and not second.in_transaction()
            asyncio.run(first.close())
            asyncio.run(second.close())
            assert client.get("/health").json() == {"status": "ok", "service": "libris-api"}
            assert client.get("/api/v1/identity/me").status_code == 401
        close.assert_awaited_once_with(app.state.database)


def test_openapi_only_describes_real_operations_and_schemas() -> None:
    with TestClient(main.create_app(Settings(_env_file=None, app_env="test"))) as client:
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert set(schema["paths"]) == {"/health", "/api/v1/identity/me"}
        assert schema["info"]["version"] == "0.1.0"
        operations = [path["get"] for path in schema["paths"].values()]
        assert len({op["operationId"] for op in operations}) == 2
        for path, model in (
            ("/health", "HealthResponse"),
            ("/api/v1/identity/me", "IdentityResponse"),
        ):
            operation = schema["paths"][path]["get"]
            assert operation["responses"]["200"]["content"]["application/json"]["schema"] == {
                "$ref": f"#/components/schemas/{model}"
            }
            assert model in schema["components"]["schemas"]
        assert schema["paths"]["/api/v1/identity/me"]["get"]["security"] == [{"HTTPBearer": []}]
        assert schema["components"]["securitySchemes"]["HTTPBearer"]["scheme"] == "bearer"
        assert not any(name.endswith("Create") for name in schema["components"]["schemas"])


@pytest.mark.parametrize("authorization", [None, "Bearer invalid-token", "Basic forged"])
def test_identity_401_cannot_be_bypassed_by_client_context(authorization: str | None) -> None:
    app = main.create_app(Settings(_env_file=None, app_env="test", oidc_enabled=True))
    headers = {"actor_id": "forged", "roles": "libris-admin", "permissions": "system:admin"}
    if authorization is not None:
        headers["Authorization"] = authorization
    with TestClient(app) as client:
        response = client.get("/api/v1/identity/me?technical_context=admin", headers=headers)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json()["code"] == "authentication.required"
    assert "forged" not in response.text and "invalid-token" not in response.text


def test_identity_response_preserves_dependency_override_boundary() -> None:
    app = main.create_app(Settings(_env_file=None, app_env="test"))
    trusted = actor(P.BIBLIOGRAPHIC_READ)
    app.dependency_overrides[get_current_actor] = lambda: trusted
    with TestClient(app) as client:
        response = client.get("/api/v1/identity/me")
    assert response.status_code == 200
    assert response.json() == {
        "actor_id": trusted.actor_id,
        "roles": [],
        "permissions": ["bibliographic:read"],
    }


@pytest.mark.parametrize("token", [None, "invalid-token"])
def test_authentication_dependency_in_isolation(token: str | None) -> None:
    app = main.create_app(Settings(_env_file=None, app_env="test", oidc_enabled=True))
    with TestClient(app):
        credentials = (
            HTTPAuthorizationCredentials(scheme="Bearer", credentials=token) if token else None
        )
        with pytest.raises(HTTPException) as caught:
            asyncio.run(
                get_current_actor(
                    credentials,
                    app.state.identity_service,
                    Request({"type": "http", "headers": []}),
                )
            )
    assert caught.value.status_code == 401
    assert caught.value.headers == {"WWW-Authenticate": "Bearer"}


@pytest.mark.parametrize("resource_name", ["works", "instances", "items", "agents", "subjects"])
def test_context_and_operation_policy_in_isolation(resource_name: str) -> None:
    authority = resource_name in {"agents", "subjects"}
    kind = ResourceKind.AUTHORITY if authority else ResourceKind.BIBLIOGRAPHIC
    operation = O.AUTHORITY_READ_EDITORIAL if authority else O.BIBLIOGRAPHIC_READ_EDITORIAL
    read = P.AUTHORITY_READ if authority else P.BIBLIOGRAPHIC_READ
    guard = get_authorization_guard()
    for grants in ((), (read,), (P.METADATA_REVISION_READ,), (P.SYSTEM_ADMIN,)):
        context = asyncio.run(get_execution_context(actor(*grants)))
        with pytest.raises(PermissionDenied) as caught:
            guard.require(context=context, operation=operation, resource=ResourceContext(kind))
        assert classify(caught.value) == (403, "authorization.denied")
    context = asyncio.run(get_execution_context(actor(read, P.METADATA_REVISION_READ)))
    guard.require(context=context, operation=operation, resource=ResourceContext(kind))
    public = O.AUTHORITY_READ_PUBLIC if authority else O.BIBLIOGRAPHIC_READ_PUBLIC
    guard.require(context=None, operation=public, resource=ResourceContext(kind, "published", 1, 1))
    with pytest.raises(PermissionDenied):
        guard.require(
            context=None, operation=public, resource=ResourceContext(kind, "published", 1, 2)
        )


@pytest.mark.parametrize(
    "method,path,status",
    [
        ("GET", "/api/v1/catalog/works", 404),
        ("POST", "/api/v1/catalog/works", 404),
        ("GET", "/api/v1/catalog/works/00000000-0000-4000-8000-000000000001", 404),
        ("POST", "/health", 405),
    ],
)
def test_http_errors_and_correlation(method: str, path: str, status: int) -> None:
    identifier = str(uuid4())
    with TestClient(main.create_app(Settings(_env_file=None, app_env="test"))) as client:
        response = client.request(method, path, headers={"X-Request-ID": identifier})
    assert response.status_code == status
    assert response.headers["content-type"] == "application/problem+json"
    assert response.headers["x-request-id"] == identifier
    problem = response.json()
    assert problem["request_id"] == identifier
    assert problem["instance"] == f"urn:uuid:{identifier}"
    assert problem["status"] == status
    assert problem["code"] == ("resource.unknown" if status == 404 else "http.405")
    if status == 405:
        assert response.headers["allow"] == "GET"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert request_id_context.get() is None


@pytest.mark.parametrize(
    "model", [WorkCreate, InstanceCreate, ItemCreate, AgentCreate, SubjectCreate]
)
def test_payload_validation_handler_in_isolation(model: type[BaseModel]) -> None:
    # No body endpoint exists in #45. Exercise Pydantic and the existing handler
    # directly; this is deliberately not claimed as catalog HTTP 422 coverage.
    with pytest.raises(ValidationError) as caught:
        model.model_validate({"secret-sentinel": "secret-sentinel"})
    identifier = str(uuid4())
    request = Request({"type": "http", "state": {"request_id": identifier}})
    response = asyncio.run(
        handle_request_validation(request, RequestValidationError(caught.value.errors()))
    )
    assert response.status_code == 422
    problem = json.loads(response.body)
    assert problem["code"] == "schema.invalid"
    assert problem["issues"]
    assert "secret-sentinel" not in response.body.decode()


@pytest.mark.parametrize(
    "path,origin,method,status",
    [
        ("/api/v1/identity/me", "http://localhost:3000", "GET", 200),
        ("/api/v1/identity/me", "https://denied.example.invalid", "GET", 400),
        ("/api/v1/identity/me", "http://localhost:3000", "PATCH", 400),
        ("/api/v1/catalog/works", "http://localhost:3000", "GET", 400),
    ],
)
def test_cors_is_not_expanded_for_future_endpoints(
    path: str,
    origin: str,
    method: str,
    status: int,
) -> None:
    settings = Settings(_env_file=None, app_env="test", cors_origins=["http://localhost:3000"])
    with TestClient(main.create_app(settings)) as client:
        response = client.options(
            path,
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": method,
                "Access-Control-Request-Headers": "Authorization, X-Request-ID",
            },
        )
    assert response.status_code == status
    assert response.headers["x-frame-options"] == "DENY"
    UUID(response.headers["x-request-id"])
    if status == 200:
        assert response.headers["access-control-allow-origin"] == origin
        assert response.headers["access-control-allow-methods"] == "GET"
        assert "access-control-allow-credentials" not in response.headers
