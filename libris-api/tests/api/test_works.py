import asyncio
from collections.abc import Mapping

from httpx import ASGITransport, AsyncClient

from app.main import app
from app.modules.identity.application.service import IdentityService
from app.modules.identity.domain.exceptions import AuthenticationError


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


def install_service(*roles: str) -> None:
    app.state.identity_service = IdentityService(
        validator=StubValidator(
            {
                "azp": "libris-web",
                "iss": "http://keycloak.localhost:8081/realms/libris",
                "sub": "cataloger-123",
                "resource_access": {"libris-api": {"roles": list(roles)}},
            }
        ),
        role_source="client",
        role_client="libris-api",
        human_client="libris-web",
        observer=NullSecuritySink(),
    )


async def post_draft(payload: dict, token: str | None = "valid-token"):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(
            "/api/v1/bibliographic/drafts", json=payload, headers=headers
        )


def draft_payload(values: dict) -> dict:
    return {
        "profileId": "bibframe-work-default",
        "profileVersion": "1.0.0",
        "values": values,
    }


def test_draft_accepts_partial_work_without_main_title() -> None:
    install_service("libris-cataloger")
    response = asyncio.run(
        post_draft(
            draft_payload(
                {
                    "subtitle": "Fundamentos e perspectivas",
                    "language": ["http://id.loc.gov/vocabulary/languages/por"],
                }
            )
        )
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Rascunho enviado com sucesso."}


def test_draft_rejects_uri_outside_the_field_vocabulary() -> None:
    install_service("libris-cataloger")
    response = asyncio.run(
        post_draft(draft_payload({"language": ["https://example.org/languages/por"]}))
    )
    assert response.status_code == 422


def test_draft_rejects_unknown_field() -> None:
    install_service("libris-cataloger")
    response = asyncio.run(post_draft(draft_payload({"unknown": "value"})))
    assert response.status_code == 422


def test_draft_requires_authentication() -> None:
    install_service("libris-cataloger")
    response = asyncio.run(post_draft(draft_payload({}), token=None))
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_draft_requires_bibliographic_create_permission() -> None:
    install_service("libris-reader")
    response = asyncio.run(post_draft(draft_payload({})))
    assert response.status_code == 403


def test_old_work_creation_route_is_not_exposed() -> None:
    transport = ASGITransport(app=app)

    async def request_old_route():
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.post("/api/v1/bibliographic/works", json={})

    assert asyncio.run(request_old_route()).status_code == 404


def test_default_work_schema_is_exposed_for_the_frontend() -> None:
    transport = ASGITransport(app=app)

    async def request_schema():
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get(
                "/api/v1/bibliographic/profile/work-default.v1.json"
            )

    response = asyncio.run(request_schema())
    assert response.status_code == 200
    assert response.json()["id"] == "bibframe-work-default"
    assert response.json()["version"] == "1.0.0"
