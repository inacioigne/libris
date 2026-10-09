import json
from datetime import UTC, datetime
from uuid import UUID

from rdflib import Graph, URIRef
from rdflib.namespace import RDF
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from libris.modules.bibliographic.domain.models import Provenance, ResourceIdentity, Revision
from libris.modules.bibliographic.infrastructure.persistence import RevisionStore
from libris.modules.bibliographic.infrastructure.rdf import BF, parse_document, serialize_document
from libris.modules.bibliographic.infrastructure.validation import PROFILE_ID, validate_monograph


def prepare_document(graph: Graph, uri: str) -> list[dict[str, object]]:
    if not any((URIRef(uri), RDF.type, kind) in graph for kind in (BF.Work, BF.Instance, BF.Item)):
        raise ValueError("A URI raiz deve identificar Work, Instance ou Item no grafo.")
    report = validate_monograph(graph)
    if not report.conforms:
        raise ValueError("Grafo não conforme ao perfil monograph-v1.")
    document = serialize_document(graph, "json-ld")
    if any("\x00" in str(term) for triple in graph for term in triple):
        raise ValueError("PostgreSQL JSONB não suporta o caractere NUL em termos RDF.")
    value: object = json.loads(document)
    if not isinstance(value, list) or not all(isinstance(node, dict) for node in value):
        raise ValueError("A representação JSON-LD expandida deve ser uma lista de nós.")
    return value


class BibliographicService:
    """Internal operations; owns transactions and never mutates earlier revisions."""

    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self.sessions = sessions
        self.store = RevisionStore()

    async def create(
        self, identity: ResourceIdentity, graph: Graph, provenance: Provenance
    ) -> Revision:
        document = prepare_document(graph, identity.uri)
        revision = Revision(identity, 1, datetime.now(UTC), provenance, PROFILE_ID)
        async with self.sessions() as session, session.begin():
            await self.store.create(session, identity)
            await self.store.save(session, revision, document)
        return revision

    async def revise(
        self, identifier: UUID, expected_revision: int, graph: Graph, provenance: Provenance
    ) -> Revision:
        async with self.sessions() as session, session.begin():
            uri = await self.store.advance(session, identifier, expected_revision)
            document = prepare_document(graph, uri)
            revision = Revision(
                ResourceIdentity(identifier, uri),
                expected_revision + 1,
                datetime.now(UTC),
                provenance,
                PROFILE_ID,
            )
            await self.store.save(session, revision, document)
        return revision

    async def read(self, identifier: UUID, number: int | None = None) -> tuple[Revision, Graph]:
        async with self.sessions() as session:
            revision, document = await self.store.get(session, identifier, number)
        return revision, parse_document(json.dumps(document), "json-ld")
