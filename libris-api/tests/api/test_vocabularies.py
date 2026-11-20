import asyncio

from httpx import ASGITransport, AsyncClient

from app.main import app


async def get_vocabulary(name: str):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get(f"/api/v1/bibliographic/vocabularies/{name}")


def test_loc_languages_returns_the_complete_versioned_catalog() -> None:
    response = asyncio.run(get_vocabulary("loc-languages"))

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    body = response.json()
    assert body["vocabulary"] == "loc-languages"
    assert body["version"] == "1.0.0"
    assert len(body["terms"]) == 487
    assert len({term["code"] for term in body["terms"]}) == 487


def test_loc_languages_uses_portuguese_and_original_labels() -> None:
    response = asyncio.run(get_vocabulary("loc-languages"))
    terms = {term["code"]: term for term in response.json()["terms"]}

    assert terms["por"] == {
        "uri": "http://id.loc.gov/vocabulary/languages/por",
        "code": "por",
        "label": "Português",
    }
    # This label has no Portuguese translation in the source catalog.
    assert terms["aar"]["label"] == "Afar"


def test_unknown_vocabulary_returns_not_found() -> None:
    response = asyncio.run(get_vocabulary("not-supported"))

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Vocabulary 'not-supported' is not available"
    }
