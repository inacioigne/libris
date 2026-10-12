"""Explicit Read DTO → owned RDF description, contract 1.0."""

from collections.abc import Iterable, Mapping
from uuid import UUID

from rdflib import BNode, Graph, Literal, URIRef
from rdflib.namespace import PROV, RDF, RDFS, SKOS

from libris.modules.bibliographic.api.schemas import (
    AgentRead,
    InstanceRead,
    ItemRead,
    SubjectRead,
    WorkRead,
)
from libris.modules.bibliographic.api.schemas.common import (
    CompatibleReference,
    LocalizedText,
    LocalReference,
    UnreconciledReference,
)
from libris.modules.bibliographic.application.relationships import ResolvedEntity
from libris.modules.bibliographic.domain.relationships import DEFAULT_REGISTRY, EntityType
from libris.modules.bibliographic.infrastructure.ownership import check_snapshot
from libris.modules.bibliographic.infrastructure.rdf import BF, RdfDocumentError, new_graph

ResourceRead = WorkRead | InstanceRead | ItemRead | AgentRead | SubjectRead
ReferenceMapping = Mapping[UUID | str, ResolvedEntity]
READ_TYPES = (WorkRead, InstanceRead, ItemRead, AgentRead, SubjectRead)


def resource_to_graph(
    resource: ResourceRead, *, references: ReferenceMapping | None = None
) -> Graph:
    """Revalidate input; references are caller-resolved stored identities, never lookups."""
    if type(resource) not in READ_TYPES:
        raise RdfDocumentError("A conversão exige um dos cinco contratos Read suportados.")
    resource = type(resource).model_validate(resource.model_dump())
    graph = new_graph()
    root = URIRef(resource.uri)
    kind = (
        EntityType.WORK
        if isinstance(resource, WorkRead)
        else EntityType.INSTANCE
        if isinstance(resource, InstanceRead)
        else EntityType.ITEM
        if isinstance(resource, ItemRead)
        else EntityType.AGENT
        if isinstance(resource, AgentRead)
        else EntityType.SUBJECT
    )
    graph.add(
        (
            root,
            RDF.type,
            SKOS.Concept
            if kind == EntityType.SUBJECT
            else BF[resource.kind if isinstance(resource, AgentRead) else kind.value],
        )
    )

    def reference(value: CompatibleReference) -> URIRef:
        if isinstance(value, UnreconciledReference):
            raise RdfDocumentError("Referência não reconciliada não é publicável.")
        if isinstance(value, LocalReference):
            if value.internal_id is not None or references is not None:
                candidates = [
                    references[key]
                    for key in (value.internal_id, value.uri)
                    if key is not None and references is not None and key in references
                ]
                if not candidates or any(entity != candidates[0] for entity in candidates):
                    raise RdfDocumentError("Referência local sem resolução consistente.")
                entity = candidates[0]
                if (
                    value.entity_type != entity.entity_type
                    or (
                        value.internal_id is not None
                        and value.internal_id != entity.identity.internal_id
                    )
                    or (value.uri is not None and value.uri != entity.identity.uri)
                ):
                    raise RdfDocumentError("Identidade local incompatível com o resolvedor.")
                return URIRef(entity.identity.uri)
            if value.uri is None:
                raise RdfDocumentError("Referência local sem URI armazenada.")
        assert value.uri is not None
        return URIRef(value.uri)

    def refs(
        node: URIRef | BNode, predicate: URIRef, values: Iterable[CompatibleReference]
    ) -> None:
        for value in values:
            graph.add((node, predicate, reference(value)))

    def texts(node: URIRef | BNode, predicate: URIRef, values: Iterable[LocalizedText]) -> None:
        for value in values:
            graph.add((node, predicate, Literal(value.value, lang=value.language)))

    def strings(node: URIRef | BNode, predicate: URIRef, values: Iterable[str]) -> None:
        for value in values:
            graph.add((node, predicate, Literal(value)))

    def auxiliary(predicate: URIRef, rdf_class: URIRef) -> BNode:
        node = BNode()
        graph.add((root, predicate, node))
        graph.add((node, RDF.type, rdf_class))
        return node

    def relation_predicate(field: str) -> URIRef:
        definitions = [
            definition
            for definition in DEFAULT_REGISTRY.entries.values()
            if definition.source == kind and definition.field == field and not definition.derived
        ]
        if len(definitions) != 1:
            raise RdfDocumentError("Campo sem relação autorizada no registro.")
        return URIRef(definitions[0].predicate)

    def relations(field: str, values: Iterable[CompatibleReference]) -> None:
        predicate = relation_predicate(field)
        definition = DEFAULT_REGISTRY.get(kind, str(predicate))
        targets = [reference(value) for value in values]
        if not definition.self_allowed and root in targets:
            raise RdfDocumentError("Autorreferência incompatível com o contrato de relações.")
        for target in targets:
            graph.add((root, predicate, target))

    if isinstance(resource, (WorkRead, InstanceRead)):
        for title in resource.title:
            node = auxiliary(BF.title, BF[title.kind])
            texts(node, BF.mainTitle, title.main_title)
            texts(node, BF.subtitle, title.subtitle)
    if isinstance(resource, (WorkRead, InstanceRead, ItemRead)):
        for note in resource.note:
            node = auxiliary(BF.note, BF.Note)
            texts(node, RDFS.label, note.label)
            strings(node, BF.noteType, note.note_type)
    if isinstance(resource, (InstanceRead, ItemRead, AgentRead)):
        for identifier in resource.identified_by:
            node = auxiliary(BF.identifiedBy, BF[identifier.kind])
            strings(node, RDF.value, [identifier.value])
            refs(node, BF.source, identifier.source)
    if isinstance(resource, WorkRead):
        refs(root, BF.language, resource.language)
        refs(root, BF.content, resource.content)
        relations("subject", resource.subject)
        relations("related_to", resource.related_to)
        relations("translation_of", resource.translation_of)
        definition = DEFAULT_REGISTRY.get(kind, str(relation_predicate("contribution")))
        for contribution in resource.contribution:
            assert definition.auxiliary_class is not None
            node = auxiliary(URIRef(definition.path[0]), URIRef(definition.auxiliary_class))
            target = reference(contribution.agent)
            if target == root:
                raise RdfDocumentError("Contribuição não admite autorreferência.")
            graph.add((node, URIRef(definition.path[1]), target))
            refs(node, BF.role, contribution.role)
        for classification in resource.classification:
            node = auxiliary(BF.classification, BF.Classification)
            strings(node, BF.classificationPortion, classification.classification_portion)
            refs(node, BF.source, classification.source)
    elif isinstance(resource, InstanceRead):
        relations("instance_of", [resource.instance_of])
        texts(root, BF.editionStatement, resource.edition_statement)
        refs(root, BF.carrier, resource.carrier)
        definition = DEFAULT_REGISTRY.get(kind, str(relation_predicate("provision_activity.agent")))
        for publication in resource.provision_activity:
            assert definition.auxiliary_class is not None
            node = auxiliary(URIRef(definition.path[0]), URIRef(definition.auxiliary_class))
            if any(reference(agent) == root for agent in publication.agent):
                raise RdfDocumentError("Publicação não admite autorreferência.")
            refs(node, URIRef(definition.path[1]), publication.agent)
            refs(node, BF.place, publication.place)
            for date in publication.date:
                graph.add(
                    (
                        node,
                        BF.date,
                        Literal(date.value, datatype=URIRef(date.datatype), normalize=False),
                    )
                )
        for extent in resource.extent:
            node = auxiliary(BF.extent, BF.Extent)
            texts(node, RDFS.label, extent.label)
    elif isinstance(resource, ItemRead):
        relations("item_of", [resource.item_of])
        relations("held_by", resource.held_by)
        texts(root, BF.custodialHistory, resource.custodial_history)
        for shelf_mark in resource.shelf_mark:
            node = auxiliary(BF.shelfMark, BF.ShelfMark)
            strings(node, RDF.value, [shelf_mark.value])
            refs(node, BF.source, shelf_mark.source)
    elif isinstance(resource, AgentRead):
        texts(root, RDFS.label, resource.authorized_name)
        texts(root, SKOS.altLabel, resource.variant_name)
        relations("related_authority", resource.related_authority)
    elif isinstance(resource, SubjectRead):
        texts(root, SKOS.prefLabel, resource.preferred_label)
        texts(root, SKOS.altLabel, resource.alternative_label)
        refs(root, SKOS.inScheme, resource.scheme)
        relations("broader", resource.broader)
        relations("related", resource.related)
    if isinstance(resource, (AgentRead, SubjectRead)):
        refs(root, RDFS.seeAlso, resource.external_reference)
    if isinstance(resource, (ItemRead, AgentRead, SubjectRead)):
        refs(root, PROV.wasDerivedFrom, resource.provenance)
    check_snapshot(graph, root)
    return graph
