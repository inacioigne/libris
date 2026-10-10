"""Authenticated actors complement technical provenance on real PostgreSQL."""

import asyncio
import os

import pytest
from rdflib import BNode, Literal, URIRef
from rdflib.namespace import RDF
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from libris.modules.bibliographic.application.service import BibliographicService
from libris.modules.bibliographic.domain.models import Provenance, ResourceIdentity
from libris.modules.bibliographic.infrastructure.rdf import BF, new_graph
from libris.modules.identity.domain.models import AuthenticatedActor, actor_identifier
from libris.modules.identity.domain.permissions import Permission

pytestmark = pytest.mark.integration


def test_revision_actor_postgres() -> None:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL exige PostgreSQL dedicado e migrado.")
    if not url.startswith("postgresql+asyncpg://"):
        pytest.fail("Integração exige PostgreSQL real.")

    async def scenario() -> None:
        engine = create_async_engine(url)
        service = BibliographicService(async_sessionmaker(engine, expire_on_commit=False))
        identity = ResourceIdentity.create("https://catalog.example.invalid/resources")
        root, title = URIRef(identity.uri), BNode()
        graph = new_graph()
        graph.add((root, RDF.type, BF.Work))
        graph.add((root, BF.title, title))
        graph.add((title, RDF.type, BF.Title))
        graph.add((title, BF.mainTitle, Literal("Teste de ator", lang="pt")))
        provenance = Provenance("fixture:synthetic", "pytest:identity")
        actor = AuthenticatedActor(
            actor_identifier("https://issuer.example.invalid", "subject"),
            "https://issuer.example.invalid",
            "subject",
            frozenset({"libris-cataloger"}),
            frozenset({Permission.METADATA_REVISION_CREATE}),
        )
        try:
            technical = await service.create(identity, graph, provenance)
            assert technical.actor_id is None
            human = await service.revise(identity.internal_id, 1, graph, provenance, actor=actor)
            stored, _ = await service.read(identity.internal_id)
            assert stored == human
            assert stored.actor_id == actor.actor_id
            assert stored.provenance == provenance
            historical, _ = await service.read(identity.internal_id, 1)
            assert historical == technical
            assert historical.actor_id is None
            second = ResourceIdentity.create("https://catalog.example.invalid/resources")
            second_graph = new_graph()
            for subject, predicate, value in graph:
                second_graph.add(
                    (URIRef(second.uri) if subject == root else subject, predicate, value)
                )
            created = await service.create(second, second_graph, provenance, actor=actor)
            assert (await service.read(second.internal_id))[0] == created
            assert created.actor_id == actor.actor_id
        finally:
            await engine.dispose()

    asyncio.run(scenario())
