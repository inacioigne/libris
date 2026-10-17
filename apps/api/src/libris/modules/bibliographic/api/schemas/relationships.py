"""Relationship contracts and deterministic collection operations, version 1.0."""

from typing import Annotated, ClassVar, Literal

from pydantic import Field, ValidationInfo, model_validator

from libris.modules.bibliographic.domain.errors import CatalogCode, CatalogError
from libris.modules.bibliographic.domain.relationships import (
    BF,
    DEFAULT_REGISTRY,
    EntityType,
    RelationRegistry,
)

from .common import (
    IRI,
    Contract,
    EntityReference,
    LocalReference,
    Text,
    UnreconciledReference,
    non_nullable_schema,
)


def registry_for(info: ValidationInfo) -> RelationRegistry:
    if isinstance(info.context, dict):
        registry = info.context.get("registry", DEFAULT_REGISTRY)
        if isinstance(registry, RelationRegistry):
            return registry
    return DEFAULT_REGISTRY


def same_reference(left: EntityReference, right: EntityReference) -> bool:
    if isinstance(left, UnreconciledReference) or isinstance(right, UnreconciledReference):
        return (
            isinstance(left, UnreconciledReference)
            and isinstance(right, UnreconciledReference)
            and (left.namespace, left.key) == (right.namespace, right.key)
        )
    if isinstance(left, LocalReference) and isinstance(right, LocalReference):
        if left.internal_id is not None and left.internal_id == right.internal_id:
            return True
    return left.uri is not None and left.uri == right.uri


class LinkBase(Contract):
    kind: Literal["direct", "contribution", "publication"]
    source: LocalReference
    target: EntityReference
    predicate: IRI

    @model_validator(mode="after")
    def check_relation(self, info: ValidationInfo) -> "LinkBase":
        definition = registry_for(info).get(self.source.entity_type, self.predicate)
        if self.target.entity_type not in definition.targets:
            raise ValueError("Destino incompatível com a relação.")
        if not definition.self_allowed and same_reference(self.source, self.target):
            raise ValueError("Autorreferência inválida.")
        if definition.auxiliary_class is not None and self.kind == "direct":
            raise ValueError("A relação exige estrutura intermediária.")
        return self


class DirectLink(LinkBase):
    kind: Literal["direct"] = "direct"


class ContributionLink(LinkBase):
    kind: Literal["contribution"] = "contribution"
    predicate: Literal["http://id.loc.gov/ontologies/bibframe/contribution"] = (
        "http://id.loc.gov/ontologies/bibframe/contribution"
    )
    role: Annotated[list[IRI], Field(min_length=1)]

    @model_validator(mode="after")
    def check_roles(self) -> "ContributionLink":
        if len(self.role) != len(set(self.role)):
            raise ValueError("Papéis duplicados.")
        return self


class PublicationLink(LinkBase):
    kind: Literal["publication"] = "publication"
    predicate: Literal["http://id.loc.gov/ontologies/bibframe/provisionActivity"] = (
        "http://id.loc.gov/ontologies/bibframe/provisionActivity"
    )
    activity_type: Literal["Publication"] = "Publication"
    activity_key: Text


Link = Annotated[DirectLink | ContributionLink | PublicationLink, Field(discriminator="kind")]


def roles(link: Link) -> frozenset[str]:
    return frozenset(link.role) if isinstance(link, ContributionLink) else frozenset()


def same_link(left: Link, right: Link) -> bool:
    if isinstance(left, PublicationLink) and isinstance(right, PublicationLink):
        if left.activity_key != right.activity_key:
            return False
    return (
        left.predicate == right.predicate
        and same_reference(left.source, right.source)
        and same_reference(left.target, right.target)
        and roles(left) == roles(right)
    )


class RelationshipCreate(Contract):
    """Complete owned collection; minima are the current candidate profile's policy."""

    allow_derived: ClassVar[bool] = False
    source: LocalReference
    links: list[Link] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_collection(self, info: ValidationInfo) -> "RelationshipCreate":
        registry = registry_for(info)
        for index, link in enumerate(self.links):
            if link.source.entity_type != self.source.entity_type or not same_reference(
                link.source, self.source
            ):
                raise ValueError("Origem do vínculo difere da coleção.")
            definition = registry.get(self.source.entity_type, link.predicate)
            if definition.derived and not self.allow_derived:
                raise ValueError("Inversas derivadas não são graváveis.")
            if any(same_link(link, previous) for previous in self.links[:index]):
                raise ValueError("Vínculo duplicado.")
        minimums = {BF + "instanceOf": 1} if self.source.entity_type == EntityType.INSTANCE else {}
        if self.source.entity_type == EntityType.ITEM:
            minimums = {BF + "itemOf": 1}
        if isinstance(info.context, dict) and "minimums" in info.context:
            minimums = info.context["minimums"]
        for (source, predicate), definition in registry.entries.items():
            if source != self.source.entity_type:
                continue
            count = sum(link.predicate == predicate for link in self.links)
            minimum = max(definition.minimum, minimums.get(predicate, 0))
            if count < minimum or (definition.maximum is not None and count > definition.maximum):
                raise ValueError(f"Cardinalidade inválida: {definition.name}.")
        return self


class RelationshipRead(RelationshipCreate):
    """Allows composed inverses, without recursively embedding descriptions."""

    allow_derived = True


class RelationshipReplace(RelationshipCreate):
    """Complete replacement of the owned relationships, not the whole RDF snapshot."""


class AddLinks(Contract):
    op: Literal["add"]
    links: Annotated[list[Link], Field(min_length=1)]


class RemoveLinks(Contract):
    op: Literal["remove"]
    links: Annotated[list[Link], Field(min_length=1)]


class ReplaceLinks(Contract):
    op: Literal["replace"]
    predicate: IRI
    links: list[Link]

    @model_validator(mode="after")
    def check_predicate(self) -> "ReplaceLinks":
        if any(link.predicate != self.predicate for link in self.links):
            raise ValueError("Substituição contém predicado diferente.")
        return self


LinkOperation = Annotated[AddLinks | RemoveLinks | ReplaceLinks, Field(discriminator="op")]


class RelationshipUpdate(Contract):
    # None is only the omission sentinel; explicit null is rejected and not advertised.
    operations: list[LinkOperation] | None = Field(
        default=None, json_schema_extra=non_nullable_schema
    )

    @model_validator(mode="before")
    @classmethod
    def reject_null(cls, value: object) -> object:
        if isinstance(value, dict) and value.get("operations", []) is None:
            raise ValueError("operations não admite null.")
        return value


def apply_relationship_update(
    current: RelationshipCreate,
    update: RelationshipUpdate,
    registry: RelationRegistry = DEFAULT_REGISTRY,
) -> RelationshipCreate:
    """Pure atomic operation: inputs unchanged; full final state always revalidated."""
    links = list(current.links)
    for operation in update.operations or []:
        for link in operation.links:
            if link.source.entity_type != current.source.entity_type or not same_reference(
                link.source, current.source
            ):
                raise CatalogError(
                    CatalogCode.REFERENCE_INVALID, "Origem da operação difere da coleção."
                )
            if registry.get(current.source.entity_type, link.predicate).derived:
                raise CatalogError(
                    CatalogCode.REFERENCE_INVALID, "Inversa derivada não é gravável."
                )
        if isinstance(operation, ReplaceLinks):
            definition = registry.get(current.source.entity_type, operation.predicate)
            if definition.derived:
                raise CatalogError(
                    CatalogCode.REFERENCE_INVALID, "Inversa derivada não é gravável."
                )
            links = [link for link in links if link.predicate != operation.predicate]
            links.extend(operation.links)
        elif isinstance(operation, AddLinks):
            links.extend(operation.links)
        else:
            for removal in operation.links:
                matches = [link for link in links if same_link(link, removal)]
                if len(matches) != 1:
                    raise CatalogError(
                        CatalogCode.REFERENCE_INVALID, "Remoção exige um vínculo existente."
                    )
                links.remove(matches[0])
    return RelationshipCreate.model_validate(
        {"source": current.source.model_dump(), "links": [link.model_dump() for link in links]},
        context={"registry": registry},
    )
