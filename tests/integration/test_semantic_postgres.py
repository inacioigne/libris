"""Run explicitly against a dedicated, migrated PostgreSQL database (never SQLite)."""

import asyncio
import os
from pathlib import Path

import pytest
from rdflib import Literal, URIRef
from rdflib.compare import isomorphic
from rdflib.namespace import DCTERMS
from sqlalchemy import select, text, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from libris.modules.bibliographic.application.service import BibliographicService
from libris.modules.bibliographic.domain.models import (
    Provenance,
    ResourceIdentity,
    StaleRevisionError,
)
from libris.modules.bibliographic.infrastructure.persistence import (
    SemanticResource,
    SemanticRevision,
)
from libris.modules.bibliographic.infrastructure.rdf import (
    new_graph,
    parse_document,
)

pytestmark = pytest.mark.integration


def test_postgres_revisions_roundtrip_and_concurrency(monkeypatch: pytest.MonkeyPatch) -> None:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL exige PostgreSQL dedicado com alembic upgrade head.")
    if not url.startswith("postgresql+asyncpg://"):
        pytest.fail("Integração exige PostgreSQL real via asyncpg.")
    asyncio.run(exercise_postgres(url, monkeypatch))


async def exercise_postgres(url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    engine = create_async_engine(url)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    service = BibliographicService(sessions)
    identity = ResourceIdentity.create("http://localhost:8000/resources")
    fixture = Path(__file__).parents[1] / "fixtures/bibliographic/book.ttl"
    original = parse_document(fixture.read_text(), "turtle")
    old_uri = URIRef("http://localhost:8000/resources/00000000-0000-4000-8000-000000000001")
    graph = new_graph()
    for s, p, o in original:
        graph.add(
            (
                URIRef(identity.uri) if s == old_uri else s,
                p,
                URIRef(identity.uri) if o == old_uri else o,
            )
        )
    provenance = Provenance("fixture:synthetic", "pytest:stage2")
    try:
        revision = await service.create(identity, graph, provenance)
        recovered, restored = await service.read(identity.internal_id)
        assert recovered == revision
        assert recovered.created_at.utcoffset().total_seconds() == 0  # type: ignore[union-attr]
        assert isomorphic(graph, restored)
        monkeypatch.setenv("RESOURCE_BASE_URI", "https://example.invalid/changed-base")
        graph.add((URIRef(identity.uri), DCTERMS.description, Literal("Revisão 2")))
        newer = await service.revise(identity.internal_id, 1, graph, provenance)
        assert newer.number == 2
        assert newer.identity == identity
        prior, old_graph = await service.read(identity.internal_id, 1)
        assert prior == revision
        assert isomorphic(old_graph, restored)
        assert len(old_graph) + 1 == len(graph)
        with pytest.raises(StaleRevisionError):
            await service.revise(identity.internal_id, 1, graph, provenance)
        invalid = new_graph()
        with pytest.raises(ValueError):
            await service.revise(identity.internal_id, 2, invalid, provenance)
        current, _ = await service.read(identity.internal_id)
        assert current.number == 2  # failed validation rolls back the CAS update
        results = await asyncio.gather(
            service.revise(identity.internal_id, 2, graph, provenance),
            service.revise(identity.internal_id, 2, graph, provenance),
            return_exceptions=True,
        )
        assert sum(isinstance(result, StaleRevisionError) for result in results) == 1
        assert sum(not isinstance(result, Exception) for result in results) == 1
        current, restored = await service.read(identity.internal_id)
        assert current.number == 3
        assert isomorphic(graph, restored)
        async with sessions() as session:
            documents = (
                await session.scalars(
                    select(SemanticRevision.document).where(
                        SemanticRevision.resource_id == identity.internal_id
                    )
                )
            ).all()
            assert len(documents) == 3
        with pytest.raises(DBAPIError):
            async with sessions() as session, session.begin():
                await session.execute(
                    update(SemanticRevision)
                    .where(SemanticRevision.resource_id == identity.internal_id)
                    .values(source="tampered")
                )
        with pytest.raises(DBAPIError):
            async with sessions() as session, session.begin():
                await session.execute(
                    text("DELETE FROM experimental_semantic_revisions WHERE resource_id = :id"),
                    {"id": identity.internal_id},
                )
        with pytest.raises(DBAPIError):
            async with sessions() as session, session.begin():
                await session.execute(
                    update(SemanticResource)
                    .where(SemanticResource.id == identity.internal_id)
                    .values(current_revision=999)
                )
        with pytest.raises(LookupError):
            await service.read(identity.internal_id, 999)
    finally:
        await engine.dispose()
