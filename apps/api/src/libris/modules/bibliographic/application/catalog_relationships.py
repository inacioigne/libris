"""Relações HTTP na unidade transacional de conteúdo existente."""

import json
from dataclasses import dataclass
from uuid import UUID

from rdflib import Graph, URIRef
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from libris.modules.bibliographic.api.schemas.common import (
    EntityReference,
    ExternalReference,
    LocalReference,
)
from libris.modules.bibliographic.api.schemas.relationships import (
    DirectLink,
    RelationshipCreate,
    RelationshipRead,
    RelationshipUpdate,
)
from libris.modules.bibliographic.application.catalog import CatalogService, CatalogView
from libris.modules.bibliographic.application.editorial_postgres import (
    PostgresReferenceResolver,
    entity_kind,
)
from libris.modules.bibliographic.application.relationships import (
    apply_resolved_relationship_update,
    validate_cycles,
)
from libris.modules.bibliographic.domain.audit import AuditEventType
from libris.modules.bibliographic.domain.errors import CatalogCode, CatalogError
from libris.modules.bibliographic.domain.models import Provenance, StaleRevisionError
from libris.modules.bibliographic.domain.relationships import DEFAULT_REGISTRY
from libris.modules.bibliographic.infrastructure.editorial import write_gate
from libris.modules.bibliographic.infrastructure.ownership import check_snapshot
from libris.modules.bibliographic.infrastructure.persistence import SemanticResource
from libris.modules.bibliographic.infrastructure.rdf import BF, parse_document
from libris.modules.bibliographic.infrastructure.relationship_graph import (
    canonical_snapshot,
    change_relationship_graph,
)
from libris.modules.bibliographic.infrastructure.serialization import ResourceRead, graph_to_read
from libris.modules.identity.application.authorization import ExecutionContext


@dataclass(frozen=True)
class RelationshipView:
    catalog: CatalogView
    relationships: RelationshipRead


async def snapshot_relationships(
    session: AsyncSession,
    graph: Graph,
    source: LocalReference,
) -> RelationshipCreate:
    resolver = PostgresReferenceResolver(session, lock=False)
    links: list[dict[str, object]] = []
    root = URIRef(str(source.uri))
    for definition in DEFAULT_REGISTRY.entries.values():
        if definition.source != source.entity_type or definition.derived:
            continue
        nodes = graph.objects(root, URIRef(definition.path[0])) if definition.path else (root,)
        for node in nodes:
            predicate = definition.path[-1] if definition.path else definition.predicate
            for target in graph.objects(node, URIRef(predicate)):
                if not isinstance(target, URIRef):
                    raise CatalogError(CatalogCode.REFERENCE_INVALID, "Destino deve ser IRI.")
                stored = await session.scalar(
                    select(SemanticResource).where(SemanticResource.uri == str(target))
                )
                resolved = (
                    await resolver.resolve(
                        LocalReference(
                            entity_type=next(iter(definition.targets)), internal_id=stored.id
                        )
                    )
                    if stored is not None
                    else None
                )
                reference: EntityReference
                if resolved:
                    reference = LocalReference(
                        entity_type=resolved.entity_type,
                        internal_id=resolved.identity.internal_id,
                        uri=resolved.identity.uri,
                    )
                else:
                    if len(definition.targets) != 1:
                        raise CatalogError(
                            CatalogCode.REFERENCE_UNVERIFIED,
                            "Tipo externo ambíguo não pode ser inferido do RDF.",
                        )
                    reference = ExternalReference(
                        entity_type=next(iter(definition.targets)), uri=str(target)
                    )
                link: dict[str, object] = {
                    "kind": "direct",
                    "source": source,
                    "target": reference,
                    "predicate": definition.predicate,
                }
                if definition.role_required:
                    link.update(
                        kind="contribution",
                        role=sorted(str(r) for r in graph.objects(node, BF.role)),
                    )
                elif definition.auxiliary_class == str(BF.Publication):
                    link.update(kind="publication", activity_key=str(node))
                links.append(link)
    return RelationshipCreate.model_validate({"source": source, "links": links})


class RelationshipService(CatalogService):
    async def _relations(
        self,
        session: AsyncSession,
        view: CatalogView,
        graph: Graph,
        *,
        inverses: bool,
    ) -> RelationshipRead:
        source = LocalReference(
            entity_type=entity_kind(check_snapshot(graph, URIRef(view.revision.identity.uri))),
            internal_id=view.revision.identity.internal_id,
            uri=view.revision.identity.uri,
        )
        own = await snapshot_relationships(session, graph, source)
        links = list(own.links)
        if inverses:
            # Only resources whose editorial content the caller may read are passed here.
            for definition in DEFAULT_REGISTRY.entries.values():
                if definition.source != source.entity_type or not definition.derived:
                    continue
                resources = (await session.scalars(select(SemanticResource))).all()
                for resource in resources:
                    revision, document = await self.store.get(session, resource.id, None)
                    child = parse_document(json.dumps(document), "json-ld")
                    if (
                        URIRef(resource.uri),
                        URIRef(str(definition.inverse)),
                        URIRef(str(source.uri)),
                    ) in child:
                        links.append(
                            DirectLink(
                                source=source,
                                predicate=definition.predicate,
                                target=LocalReference(
                                    entity_type=entity_kind(
                                        check_snapshot(child, URIRef(resource.uri))
                                    ),
                                    internal_id=revision.identity.internal_id,
                                    uri=resource.uri,
                                ),
                            )
                        )
        return RelationshipRead(
            source=source, links=sorted(links, key=lambda link: link.model_dump_json())
        )

    async def relationships(
        self,
        identifier: UUID,
        profile: str,
        model: type[ResourceRead],
        context: ExecutionContext,
        *,
        editing: bool = False,
        inverses: bool = False,
    ) -> RelationshipView:
        self.require_operation(context, profile, "update" if editing else "read", identifier)
        async with self.sessions() as session, session.begin():
            await write_gate(session)
            view, graph = await self._current(session, identifier, model, context, editing=editing)
            result = await self._relations(
                session, view, canonical_snapshot(graph), inverses=inverses
            )
        return RelationshipView(view, result)

    async def update_relationships(
        self,
        identifier: UUID,
        update: RelationshipUpdate,
        expected: CatalogView,
        context: ExecutionContext,
    ) -> RelationshipView:
        self.require_operation(context, expected.revision.profile, "update", identifier)
        actor_id, actor_type = self._audit_context(context)
        async with self.sessions() as session, session.begin():
            await write_gate(session, editorial=True)
            current, graph = await self._current(
                session, identifier, type(expected.resource), context, editing=True
            )
            if (
                current.revision != expected.revision
                or current.editorial_version != expected.editorial_version
            ):
                raise StaleRevisionError("Precondição obsoleta.")
            graph = canonical_snapshot(graph)
            own = await self._relations(session, current, graph, inverses=False)
            before = RelationshipCreate.model_validate(own.model_dump())
            after, _ = await apply_resolved_relationship_update(
                before,
                update,
                PostgresReferenceResolver(session),
            )
            closure = list(after.links)
            # Gate exclusivo estabiliza o fecho local até o commit.
            pending = list(after.links)
            visited: set[tuple[str, str]] = set()
            while pending:
                link = pending.pop()
                if not DEFAULT_REGISTRY.get(link.source.entity_type, link.predicate).acyclic:
                    continue
                if not isinstance(link.target, LocalReference):
                    continue
                key = (str(link.target.uri), link.predicate)
                if key in visited or link.target.internal_id == identifier:
                    continue
                visited.add(key)
                assert link.target.internal_id is not None
                _, document = await self.store.get(session, link.target.internal_id, None)
                dependency = parse_document(json.dumps(document), "json-ld")
                collection = await snapshot_relationships(session, dependency, link.target)
                edges = [edge for edge in collection.links if edge.predicate == link.predicate]
                closure.extend(edges)
                pending.extend(edges)
            validate_cycles(closure)
            changed = change_relationship_graph(graph, before, after)
            projected = graph_to_read(changed, current.revision.identity)
            revision = await self._revise(
                session,
                identifier,
                expected.revision.number,
                changed,
                Provenance("catalog", "http:relationships"),
                actor_id,
                actor_type,
                AuditEventType.REVISED,
                expected_editorial_version=expected.editorial_version or 1,
                context=context,
            )
            view = CatalogView(revision, projected, (expected.editorial_version or 1) + 1)
            result = await self._relations(
                session, view, canonical_snapshot(changed), inverses=False
            )
        return RelationshipView(view, result)
