import asyncio

from httpx import ASGITransport, AsyncClient

from app.main import app


VALID_WORK = {
    "title": "Ecologia da Amazônia",
    "language": "pt-BR",
    "contributors": [],
    "subjectIds": [],
    "profile": {"id": "title-v1", "version": "1.0.0"},
}


async def post_work(payload: dict):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post("/api/v1/works", json=payload)


def test_create_work_is_exposed_as_a_provisional_endpoint() -> None:
    response = asyncio.run(post_work(VALID_WORK))

    assert response.status_code == 501
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json() == {
        "type": "about:blank",
        "title": "Not Implemented",
        "status": 501,
        "detail": "Work creation is not implemented yet.",
    }


def test_create_work_validates_the_proposed_request_contract() -> None:
    response = asyncio.run(post_work({"profile": VALID_WORK["profile"]}))

    assert response.status_code == 422
