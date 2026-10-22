import asyncio
from uuid import UUID

from httpx import ASGITransport, AsyncClient

from app.main import app


CATALOGER_ID = "1f95cb0d-ef38-4f0d-a9bf-8918222ee429"


async def post_draft(*, payload: dict | None = None, cataloger_id: str = CATALOGER_ID):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        kwargs = {"headers": {"X-Cataloger-Id": cataloger_id}}
        if payload is not None:
            kwargs["json"] = payload
        return await client.post("/api/v1/bibliographic/drafts", **kwargs)


def test_create_draft_accepts_an_empty_object_and_associates_the_cataloger() -> None:
    response = asyncio.run(post_draft(payload={}))

    assert response.status_code == 201
    assert response.headers["content-type"] == "application/json"
    body = response.json()
    assert UUID(body["id"])
    assert body["catalogerId"] == CATALOGER_ID
    assert response.headers["location"] == f"/api/v1/bibliographic/drafts/{body['id']}"


def test_create_draft_accepts_an_absent_body() -> None:
    response = asyncio.run(post_draft())

    assert response.status_code == 201


def test_create_draft_rejects_cataloging_fields_for_now() -> None:
    response = asyncio.run(post_draft(payload={"title": "Not implemented yet"}))

    assert response.status_code == 422


def test_create_draft_requires_the_cataloger_identity() -> None:
    transport = ASGITransport(app=app)

    async def request_without_cataloger():
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.post("/api/v1/bibliographic/drafts", json={})

    response = asyncio.run(request_without_cataloger())

    assert response.status_code == 422


def test_old_work_creation_route_is_not_exposed() -> None:
    transport = ASGITransport(app=app)

    async def request_old_route():
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.post("/api/v1/bibliographic/works", json={})

    response = asyncio.run(request_old_route())

    assert response.status_code == 404
