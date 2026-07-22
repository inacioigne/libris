"""
Testes para o router de works (works.py).

O router usa AsyncSession, então os testes usam httpx.AsyncClient +
pytest-asyncio. create_work é mockada; o link_agent_to_work usa um
mock de AsyncSession para simular commit/rollback.
"""
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

# from works import router
from routes.works import router
import routes.works as works_module
from core.db import get_db


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    return db


@pytest.fixture
async def client(app, mock_db):
    app.dependency_overrides[get_db] = lambda: mock_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_create_work_success(client, monkeypatch):
    fake_work = {"id": str(uuid.uuid4()), "title": "Minha Obra"}
    monkeypatch.setattr(
        works_module, "create_work", AsyncMock(return_value=fake_work)
    )

    payload = {"title": "Minha Obra"}
    response = await client.post("/works/", json=payload)

    assert response.status_code == 201
    response_json = response.json()
    assert response_json["id"] == fake_work["id"]
    assert response_json["title"] == fake_work["title"]
    assert response_json["subject"] is None
    assert response_json["type"] is None


@pytest.mark.asyncio
async def test_link_agent_to_work_success(client, mock_db):
    work_id = str(uuid.uuid4())
    agent_id = str(uuid.uuid4())
    payload = {"agent_id": agent_id, "role": "autor"}
    response = await client.post(f"/works/{work_id}/agents", json=payload)

    assert response.status_code == 201
    assert response.json()["work_id"] == work_id
    assert response.json()["agent_id"] == agent_id
    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited_once()
    mock_db.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_link_agent_to_work_conflict_returns_400(client, mock_db):
    mock_db.commit.side_effect = Exception("duplicate key")

    work_id = str(uuid.uuid4())
    agent_id = str(uuid.uuid4())
    payload = {"agent_id": agent_id, "role": "autor"}
    response = await client.post(f"/works/{work_id}/agents", json=payload)

    assert response.status_code == 400
    assert "já existe" in response.json()["detail"].lower()
    mock_db.rollback.assert_awaited_once()