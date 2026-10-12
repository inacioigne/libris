"""Versioned semantic metadata. No HTTP, DTO, ORM or search dependencies."""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType


class EntityType(StrEnum):
    WORK = "Work"
    INSTANCE = "Instance"
    ITEM = "Item"
    AGENT = "Agent"
    SUBJECT = "Subject"


BF = "http://id.loc.gov/ontologies/bibframe/"
SKOS = "http://www.w3.org/2004/02/skos/core#"
REGISTRY_VERSION = "1.0"


@dataclass(frozen=True)
class RelationDefinition:
    name: str
    definition: str
    source: EntityType
    targets: frozenset[EntityType]
    predicate: str
    field: str
    inverse: str | None = None
    maximum: int | None = None
    derived: bool = False
    self_allowed: bool = False
    acyclic: bool = False
    path: tuple[str, ...] = ()
    auxiliary_class: str | None = None
    role_required: bool = False
    minimum: int = 0
    symmetric: bool = False


WORK, INSTANCE, ITEM, AGENT, SUBJECT = EntityType


def relation(
    name: str,
    definition: str,
    source: EntityType,
    target: EntityType,
    predicate: str,
    field: str,
    *,
    inverse: str | None = None,
    maximum: int | None = None,
    derived: bool = False,
    acyclic: bool = False,
    path: tuple[str, ...] = (),
    auxiliary_class: str | None = None,
    role_required: bool = False,
    symmetric: bool = False,
) -> RelationDefinition:
    return RelationDefinition(
        name,
        definition,
        source,
        frozenset([target]),
        predicate,
        field,
        inverse,
        maximum,
        derived,
        False,
        acyclic,
        path,
        auxiliary_class,
        role_required,
        symmetric=symmetric,
    )


INITIAL_RELATIONS = (
    relation(
        "instance_of",
        "Materialização da obra.",
        INSTANCE,
        WORK,
        BF + "instanceOf",
        "instance_of",
        inverse=BF + "hasInstance",
        maximum=1,
    ),
    relation(
        "has_instance",
        "Instâncias da obra, derivadas dos filhos.",
        WORK,
        INSTANCE,
        BF + "hasInstance",
        "has_instance",
        inverse=BF + "instanceOf",
        derived=True,
    ),
    relation(
        "item_of",
        "Cópia bibliográfica da instância.",
        ITEM,
        INSTANCE,
        BF + "itemOf",
        "item_of",
        inverse=BF + "hasItem",
        maximum=1,
    ),
    relation(
        "has_item",
        "Cópias da instância, derivadas dos filhos.",
        INSTANCE,
        ITEM,
        BF + "hasItem",
        "has_item",
        inverse=BF + "itemOf",
        derived=True,
    ),
    relation(
        "contribution",
        "Agente e seus papéis na obra.",
        WORK,
        AGENT,
        BF + "contribution",
        "contribution",
        path=(BF + "contribution", BF + "agent"),
        auxiliary_class=BF + "Contribution",
        role_required=True,
    ),
    relation(
        "subject",
        "Conceito utilizado como assunto da obra.",
        WORK,
        SUBJECT,
        BF + "subject",
        "subject",
    ),
    relation(
        "work_related_to",
        "Obra bibliograficamente relacionada.",
        WORK,
        WORK,
        BF + "relatedTo",
        "related_to",
        symmetric=True,
    ),
    relation(
        "translation_of",
        "Obra de origem da tradução.",
        WORK,
        WORK,
        BF + "translationOf",
        "translation_of",
        inverse=BF + "translation",
        acyclic=True,
    ),
    relation(
        "instance_related_to",
        "Instância bibliograficamente relacionada.",
        INSTANCE,
        INSTANCE,
        BF + "relatedTo",
        "related_to",
        symmetric=True,
    ),
    relation(
        "publication_agent",
        "Publicador na atividade de publicação.",
        INSTANCE,
        AGENT,
        BF + "provisionActivity",
        "provision_activity.agent",
        path=(BF + "provisionActivity", BF + "agent"),
        auxiliary_class=BF + "Publication",
    ),
    relation(
        "held_by",
        "Agente detentor do Item, sem estado operacional.",
        ITEM,
        AGENT,
        BF + "heldBy",
        "held_by",
    ),
    relation(
        "broader",
        "Conceito hierarquicamente mais amplo.",
        SUBJECT,
        SUBJECT,
        SKOS + "broader",
        "broader",
        inverse=SKOS + "narrower",
        acyclic=True,
    ),
    relation(
        "subject_related",
        "Conceito associativamente relacionado.",
        SUBJECT,
        SUBJECT,
        SKOS + "related",
        "related",
        symmetric=True,
    ),
    RelationDefinition(
        "related_authority",
        "Autoridade relacionada, sem equivalência.",
        AGENT,
        frozenset([AGENT, SUBJECT]),
        "http://purl.org/dc/terms/relation",
        "related_authority",
    ),
)


class RelationRegistry:
    """Trusted configuration, never populated from a request payload."""

    def __init__(self, definitions: tuple[RelationDefinition, ...] = INITIAL_RELATIONS) -> None:
        entries: dict[tuple[EntityType, str], RelationDefinition] = {}
        names: set[str] = set()
        for entry in definitions:
            if entry.name in names or (entry.source, entry.predicate) in entries:
                raise ValueError("Relação duplicada no registro.")
            if entry.minimum < 0 or (entry.maximum is not None and entry.maximum < entry.minimum):
                raise ValueError("Cardinalidade inválida no registro.")
            names.add(entry.name)
            entries[entry.source, entry.predicate] = entry
        self.entries: Mapping[tuple[EntityType, str], RelationDefinition] = MappingProxyType(
            entries
        )

    def get(self, source: EntityType, predicate: str) -> RelationDefinition:
        try:
            return self.entries[source, predicate]
        except KeyError as error:
            raise ValueError("Predicado não autorizado para a origem.") from error

    def extend(self, definition: RelationDefinition, namespace: str) -> "RelationRegistry":
        from libris.modules.bibliographic.domain.profiles import absolute_iri

        absolute_iri(namespace)
        absolute_iri(definition.predicate)
        if (
            not namespace.endswith(("/", "#", ":"))
            or namespace.startswith((BF, SKOS))
            or definition.predicate.startswith((BF, SKOS))
            or not definition.predicate.startswith(namespace)
        ):
            raise ValueError("Extensão exige namespace próprio e não redefine BIBFRAME/SKOS.")
        if definition.path or definition.auxiliary_class or definition.role_required:
            raise ValueError("Esta extensão suporta relações diretas; auxiliares exigem contrato.")
        return RelationRegistry((*self.entries.values(), definition))


DEFAULT_REGISTRY = RelationRegistry()
