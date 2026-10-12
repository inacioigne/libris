"""Referential integrity boundary; callers supply resolution in their transaction."""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol

from libris.modules.bibliographic.api.schemas.common import (
    EntityReference,
    ExternalReference,
    LocalReference,
    UnreconciledReference,
)
from libris.modules.bibliographic.api.schemas.relationships import (
    Link,
    PublicationLink,
    RelationshipCreate,
    RelationshipUpdate,
    apply_relationship_update,
    roles,
    same_reference,
)
from libris.modules.bibliographic.domain.errors import CatalogCode, CatalogError
from libris.modules.bibliographic.domain.models import ResourceIdentity
from libris.modules.bibliographic.domain.relationships import (
    BF,
    DEFAULT_REGISTRY,
    EntityType,
    RelationRegistry,
)


@dataclass(frozen=True)
class ResolvedEntity:
    identity: ResourceIdentity
    entity_type: EntityType
    agent_kind: str | None = None


class ReferenceResolver(Protocol):
    async def resolve(self, reference: LocalReference) -> ResolvedEntity | None:
        """Resolve by ID/URI; return stored identity, never reconstruct a URI."""
        ...


@dataclass(frozen=True)
class IntegrityReport:
    pending: tuple[ExternalReference | UnreconciledReference, ...]


async def validate_references(
    collection: RelationshipCreate,
    resolver: ReferenceResolver,
    *,
    allow_unreconciled: bool = False,
    allowed_roles: frozenset[str] | None = None,
    registry: RelationRegistry = DEFAULT_REGISTRY,
) -> IntegrityReport:
    """No remote requests, persistence or commit. Does not replace final SHACL validation."""
    pending: list[ExternalReference | UnreconciledReference] = []

    async def resolve(reference: EntityReference) -> ResolvedEntity | None:
        if isinstance(reference, UnreconciledReference):
            if not allow_unreconciled:
                raise CatalogError(
                    CatalogCode.REFERENCE_INVALID,
                    "Referência não reconciliada exige política de rascunho.",
                )
            pending.append(reference)
            return None
        if isinstance(reference, ExternalReference):
            pending.append(reference)
            return None
        entity = await resolver.resolve(reference)
        if entity is None:
            raise CatalogError(CatalogCode.REFERENCE_INVALID, "Referência local inexistente.")
        if reference.entity_type != entity.entity_type:
            raise CatalogError(
                CatalogCode.REFERENCE_INVALID, "Tipo real da referência é incompatível."
            )
        if (
            reference.internal_id is not None
            and reference.internal_id != entity.identity.internal_id
        ):
            raise CatalogError(
                CatalogCode.REFERENCE_INVALID, "UUID e URI identificam entidades diferentes."
            )
        if reference.uri is not None and reference.uri != entity.identity.uri:
            raise CatalogError(
                CatalogCode.REFERENCE_INVALID, "URI difere da identidade armazenada."
            )
        return entity

    collection = type(collection).model_validate(
        collection.model_dump(), context={"registry": registry}
    )
    origin = await resolve(collection.source)
    assert origin is not None  # source is structurally local
    seen: set[tuple[str, str, frozenset[str], str | None]] = set()
    for link in collection.links:
        link_origin = await resolve(link.source)
        if link_origin != origin:
            raise CatalogError(CatalogCode.REFERENCE_INVALID, "Origem real difere da coleção.")
        target = await resolve(link.target)
        if target is not None:
            if (
                not registry.get(origin.entity_type, link.predicate).self_allowed
                and origin.identity.internal_id == target.identity.internal_id
            ):
                raise CatalogError(
                    CatalogCode.REFERENCE_INVALID, "Autorreferência por alias de identidade."
                )
            if link.predicate == BF + "heldBy" and target.agent_kind != "Organization":
                raise CatalogError(
                    CatalogCode.REFERENCE_INVALID,
                    "O perfil candidato exige Organization em held_by.",
                )
            target_key = target.identity.uri
        elif isinstance(link.target, UnreconciledReference):
            target_key = repr((link.target.namespace, link.target.key))
        else:
            target_key = str(link.target.uri)
        key = (
            link.predicate,
            target_key,
            roles(link),
            link.activity_key if isinstance(link, PublicationLink) else None,
        )
        if key in seen:
            raise CatalogError(CatalogCode.CONFLICT, "Vínculo duplicado após resolução.")
        seen.add(key)
        if allowed_roles is not None and not roles(link).issubset(allowed_roles):
            raise CatalogError(CatalogCode.PROFILE_POLICY, "Papel não autorizado pelo perfil.")
    return IntegrityReport(tuple(pending))


def validate_cycles(
    links: Iterable[Link],
    registry: RelationRegistry = DEFAULT_REGISTRY,
) -> None:
    """Check a supplied resolved closure, including the proposed final relationships.

    The caller must load the transitive closure in the same transaction. A partial
    graph cannot establish global absence of cycles; this function never claims it.
    """
    edges = list(links)
    for edge in edges:
        definition = registry.get(edge.source.entity_type, edge.predicate)
        if not definition.acyclic:
            continue
        pending: list[EntityReference] = [edge.target]
        visited: list[EntityReference] = []
        while pending:
            node = pending.pop()
            if same_reference(node, edge.source):
                raise CatalogError(CatalogCode.REFERENCE_INVALID, "Ciclo semanticamente inválido.")
            if any(same_reference(node, previous) for previous in visited):
                continue
            visited.append(node)
            pending.extend(
                other.target
                for other in edges
                if other.predicate == edge.predicate and same_reference(other.source, node)
            )


async def apply_resolved_relationship_update(
    current: RelationshipCreate,
    update: RelationshipUpdate,
    resolver: ReferenceResolver,
    *,
    registry: RelationRegistry = DEFAULT_REGISTRY,
    allow_unreconciled: bool = False,
    allowed_roles: frozenset[str] | None = None,
) -> tuple[RelationshipCreate, IntegrityReport]:
    """Canonicalize local aliases, apply operations and validate before a future write.

    The caller provides transaction-scoped resolution and validates global cycles,
    SHACL and the expected revision before committing a new immutable snapshot.
    """

    async def canonical(reference: LocalReference) -> LocalReference:
        entity = await resolver.resolve(reference)
        if entity is None:
            raise CatalogError(CatalogCode.REFERENCE_INVALID, "Referência local inexistente.")
        if (
            entity.entity_type != reference.entity_type
            or (
                reference.internal_id is not None
                and reference.internal_id != entity.identity.internal_id
            )
            or (reference.uri is not None and reference.uri != entity.identity.uri)
        ):
            raise CatalogError(CatalogCode.REFERENCE_INVALID, "Identidade local incompatível.")
        return LocalReference(
            entity_type=entity.entity_type,
            internal_id=entity.identity.internal_id,
            uri=entity.identity.uri,
        )

    async def normalize(link: Link) -> Link:
        source = await canonical(link.source)
        target = (
            await canonical(link.target) if isinstance(link.target, LocalReference) else link.target
        )
        return type(link).model_validate(
            link.model_dump() | {"source": source.model_dump(), "target": target.model_dump()},
            context={"registry": registry},
        )

    source = await canonical(current.source)
    links = [await normalize(link) for link in current.links]
    state = RelationshipCreate.model_validate(
        {"source": source.model_dump(), "links": [link.model_dump() for link in links]},
        context={"registry": registry},
    )
    operations: list[dict[str, object]] = []
    for operation in update.operations or []:
        normalized = [await normalize(link) for link in operation.links]
        operations.append(
            operation.model_dump() | {"links": [link.model_dump() for link in normalized]}
        )
    patch = RelationshipUpdate.model_validate(
        {"operations": operations},
        context={"registry": registry},
    )
    result = apply_relationship_update(state, patch, registry)
    report = await validate_references(
        result,
        resolver,
        registry=registry,
        allow_unreconciled=allow_unreconciled,
        allowed_roles=allowed_roles,
    )
    return result, report
