import json
from datetime import UTC, datetime
from uuid import UUID

from rdflib import Graph, URIRef
from rdflib.namespace import RDF
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from libris.modules.bibliographic.domain.models import (
    Provenance,
    ResourceIdentity,
    Revision,
    StaleRevisionError,
)
from libris.modules.bibliographic.infrastructure.ownership import check_snapshot
from libris.modules.bibliographic.infrastructure.persistence import RevisionStore
from libris.modules.bibliographic.infrastructure.rdf import BF, parse_document, serialize_document
from libris.modules.bibliographic.infrastructure.validation import (
    AUTHORITY_PROFILE_ID,
    INSTITUTIONAL_PROFILE_ID,
    PROFILE_ID,
    validate_profile,
)


def prepare_document(graph: Graph, uri: str, profile: str = PROFILE_ID) -> list[dict[str, object]]:
    if profile == PROFILE_ID:
        if not any(
            (URIRef(uri), RDF.type, kind) in graph for kind in (BF.Work, BF.Instance, BF.Item)
        ):
            raise ValueError("A URI raiz deve identificar Work, Instance ou Item no grafo.")
    else:
        kind = check_snapshot(graph, URIRef(uri))
        bibliographic = kind in (BF.Work, BF.Instance, BF.Item)
        if (profile == INSTITUTIONAL_PROFILE_ID and not bibliographic) or (
            profile == AUTHORITY_PROFILE_ID and bibliographic
        ):
            raise ValueError("Tipo da raiz incompatível com o perfil.")
    report = validate_profile(graph, profile)
    if not report.conforms:
        raise ValueError(f"Grafo não conforme ao perfil {profile}.")
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
        self,
        identity: ResourceIdentity,
        graph: Graph,
        provenance: Provenance,
        *,
        profile: str = PROFILE_ID,
    ) -> Revision:
        document = prepare_document(graph, identity.uri, profile)
        revision = Revision(identity, 1, datetime.now(UTC), provenance, profile)
        async with self.sessions() as session, session.begin():
            await self.store.create(session, identity)
            await self.store.save(session, revision, document)
        return revision

    async def revise(
        self, identifier: UUID, expected_revision: int, graph: Graph, provenance: Provenance
    ) -> Revision:
        if expected_revision < 1:
            raise ValueError("A revisão esperada deve ser positiva.")
        async with self.sessions() as session, session.begin():
            # CAS below remains the arbiter if another transaction advances after this read.
            try:
                previous, prior_document = await self.store.get(session, identifier, None)
            except LookupError as exc:
                raise StaleRevisionError("Recurso ausente; recarregue o registro.") from exc
            uri = await self.store.advance(session, identifier, expected_revision)
            document = prepare_document(graph, uri, previous.profile)
            if previous.profile != PROFILE_ID:
                prior_graph = parse_document(json.dumps(prior_document), "json-ld")
                if check_snapshot(prior_graph, URIRef(uri)) != check_snapshot(graph, URIRef(uri)):
                    raise ValueError("O tipo da identidade não muda entre revisões.")
            revision = Revision(
                ResourceIdentity(identifier, uri),
                expected_revision + 1,
                datetime.now(UTC),
                provenance,
                previous.profile,
            )
            await self.store.save(session, revision, document)
        return revision

    async def read(self, identifier: UUID, number: int | None = None) -> tuple[Revision, Graph]:
        async with self.sessions() as session:
            revision, document = await self.store.get(session, identifier, number)
        return revision, parse_document(json.dumps(document), "json-ld")
