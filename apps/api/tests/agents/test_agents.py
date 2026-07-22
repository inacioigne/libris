"""
Testes para o router de agents (agents.py) - versão assíncrona.

Usa httpx.AsyncClient + pytest-asyncio e mock de AsyncSession,
seguindo o mesmo padrão de test_works.py.
"""
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from routes.agents import router
import routes.agents as agents_module
from core.db import get_db


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.add = MagicMock()
    db.commit = AsyncMock()

    async def fake_refresh(obj):
        obj.id = uuid.uuid4()
    db.refresh = AsyncMock(side_effect=fake_refresh)
    return db


@pytest.fixture
async def client(app, mock_db):
    app.dependency_overrides[get_db] = lambda: mock_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_create_agent_success(client, mock_db, monkeypatch):
    monkeypatch.setattr(
        agents_module, "existing_agent", AsyncMock(return_value=None)
    )

    payload = {"name": "Agente Teste", "type": "bot", "identifier": "agente-1"}
    response = await client.post("/agents/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Agente Teste"
    assert data["identifier"] == "agente-1"

    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited_once()
    mock_db.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_agent_without_identifier_skips_duplicate_check(
    client, mock_db, monkeypatch
):
    existing_agent_mock = AsyncMock(return_value=None)
    monkeypatch.setattr(agents_module, "existing_agent", existing_agent_mock)

    payload = {"name": "Sem Identifier", "type": "bot", "identifier": None}
    response = await client.post("/agents/", json=payload)

    assert response.status_code == 201
    existing_agent_mock.assert_not_awaited()  # não checa duplicidade sem identifier


@pytest.mark.asyncio
async def test_create_agent_duplicate_identifier_returns_400(
    client, mock_db, monkeypatch
):
    monkeypatch.setattr(
        agents_module, "existing_agent", AsyncMock(return_value=MagicMock())
    )

    payload = {"name": "Duplicado", "type": "bot", "identifier": "ja-existe"}
    response = await client.post("/agents/", json=payload)

    assert response.status_code == 400
    assert "Já existe um agente" in response.json()["detail"]
    mock_db.add.assert_not_called()
    mock_db.commit.assert_not_awaited()