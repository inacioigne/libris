import asyncio

from httpx import ASGITransport, AsyncClient

from app.main import app


VALID_WORK = {
    "title": [
        {
            "kind": "Title",
            "main_title": [
                {"value": "Ecologia da Amazônia", "language": "pt-BR"}
            ],
            "subtitle": [],
        }
    ],
    "language": [{"uri": "http://id.loc.gov/vocabulary/languages/por"}],
}


async def post_work(payload: dict):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post("/api/v1/bibliographic/works", json=payload)


def test_create_work_returns_the_validated_payload_with_not_implemented_status() -> None:
    response = asyncio.run(post_work(VALID_WORK))

    assert response.status_code == 501
    assert response.headers["content-type"] == "application/json"
    assert response.json() == {
        **VALID_WORK,
        "content": [],
        "contribution": [],
        "subject": [],
        "classification": [],
        "related_to": [],
        "translation_of": [],
        "note": [],
    }


def test_create_work_validates_the_proposed_request_contract() -> None:
    response = asyncio.run(post_work({"language": VALID_WORK["language"]}))

    assert response.status_code == 422
