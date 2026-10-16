"""Stored RDF → public projection; record consumed terms for conservative patches."""

import json
from collections.abc import Callable, Sequence

from rdflib import BNode, Graph, Literal, URIRef
from rdflib.namespace import PROV, RDF, RDFS, SKOS, XSD
from rdflib.term import Node

from libris.modules.bibliographic.api.schemas import (
    AgentRead,
    InstanceRead,
    ItemRead,
    SubjectRead,
    WorkRead,
)
from libris.modules.bibliographic.domain.models import ResourceIdentity
from libris.modules.bibliographic.domain.relationships import DEFAULT_REGISTRY, EntityType
from libris.modules.bibliographic.infrastructure.ownership import check_snapshot
from libris.modules.bibliographic.infrastructure.rdf import BF, RdfDocumentError

from .mapping import ResourceRead


class GraphProjection:
    """One read, including exact field boundaries; never mutates the snapshot."""

    def __init__(self, graph: Graph, identity: ResourceIdentity) -> None:
        self.graph = graph
        self.root = URIRef(identity.uri)
        self.consumed: set[tuple[Node, Node, Node]] = set()
        self.fields: dict[str, URIRef] = {}
        self.kind = check_snapshot(graph, self.root)
        self.resource = self._read(identity)

    def objects(self, node: Node, predicate: URIRef) -> list[Node]:
        values = sorted(self.graph.objects(node, predicate), key=lambda term: term.n3())
        self.consumed.update((node, predicate, value) for value in values)
        return values

    def one(self, values: Sequence[Node]) -> Node:
        if len(values) != 1:
            raise RdfDocumentError("A projeção exige cardinalidade unitária.")
        return values[0]

    def text(self, value: Node) -> dict[str, object]:
        if not isinstance(value, Literal) or value.datatype not in (
            None,
            XSD.string,
            RDF.langString,
        ):
            raise RdfDocumentError("Literal não representável no contrato textual.")
        if value.datatype == RDF.langString and value.language is None:
            raise RdfDocumentError("rdf:langString exige uma tag de idioma.")
        return {"value": str(value), "language": value.language}

    def string(self, value: Node) -> str:
        text = self.text(value)
        if text["language"] is not None:
            raise RdfDocumentError("O campo não admite idioma.")
        return str(value)

    def reference(self, value: Node) -> dict[str, object]:
        # RDF records an IRI, not locality, reconciliation metadata or a UUID.
        if not isinstance(value, URIRef):
            raise RdfDocumentError("Referência deve ser uma IRI.")
        return {"uri": str(value)}

    def values(
        self, node: Node, predicate: URIRef, convert: Callable[[Node], object]
    ) -> list[object]:
        return sorted(
            [convert(value) for value in self.objects(node, predicate)],
            key=lambda value: json.dumps(value, sort_keys=True, ensure_ascii=False),
        )

    def date(self, value: Node) -> dict[str, object]:
        if not isinstance(value, Literal) or value.language is not None:
            raise RdfDocumentError("Data deve ser literal sem idioma.")
        return {"value": str(value), "datatype": str(value.datatype or XSD.string)}

    def auxiliary(self, value: Node, field: str) -> dict[str, object]:
        if not isinstance(value, (BNode, URIRef)) or (
            isinstance(value, URIRef) and not str(value).startswith(f"{self.root}#")
        ):
            raise RdfDocumentError("Auxiliar deve pertencer ao snapshot.")
        classes = {
            "title": (BF.Title, BF.VariantTitle),
            "note": (BF.Note,),
            "identified_by": (BF.Identifier, BF.Local, BF.Isbn),
            "contribution": (BF.Contribution,),
            "classification": (BF.Classification,),
            "provision_activity": (BF.Publication,),
            "extent": (BF.Extent,),
            "shelf_mark": (BF.ShelfMark,),
        }[field]
        present = [kind for kind in classes if (value, RDF.type, kind) in self.graph]
        kind = self.one(present)
        self.consumed.add((value, RDF.type, kind))
        result: dict[str, object] = {}
        if field in ("title", "identified_by"):
            result["kind"] = str(kind).removeprefix(str(BF))
        if field == "title":
            result["main_title"] = self.values(value, BF.mainTitle, self.text)
            result["subtitle"] = self.values(value, BF.subtitle, self.text)
        elif field in ("note", "extent"):
            result["label"] = self.values(value, RDFS.label, self.text)
            if field == "note":
                result["note_type"] = self.values(value, BF.noteType, self.string)
        elif field in ("identified_by", "shelf_mark"):
            result["value"] = self.string(self.one(self.objects(value, RDF.value)))
            result["source"] = self.values(value, BF.source, self.reference)
        elif field == "classification":
            result["classification_portion"] = self.values(
                value, BF.classificationPortion, self.string
            )
            result["source"] = self.values(value, BF.source, self.reference)
        elif field == "contribution":
            definition = DEFAULT_REGISTRY.get(EntityType.WORK, str(BF.contribution))
            result["agent"] = self.reference(
                self.one(self.objects(value, URIRef(definition.path[1])))
            )
            result["role"] = self.values(value, BF.role, self.reference)
        elif field == "provision_activity":
            definition = DEFAULT_REGISTRY.get(EntityType.INSTANCE, str(BF.provisionActivity))
            result["agent"] = self.values(value, URIRef(definition.path[1]), self.reference)
            result["place"] = self.values(value, BF.place, self.reference)
            result["date"] = self.values(value, BF.date, self.date)
        if field in ("contribution", "provision_activity"):
            definition = DEFAULT_REGISTRY.get(
                EntityType.WORK if field == "contribution" else EntityType.INSTANCE,
                str(BF.contribution if field == "contribution" else BF.provisionActivity),
            )
            if (
                not definition.self_allowed
                and (value, URIRef(definition.path[1]), self.root) in self.graph
            ):
                raise RdfDocumentError("Autorreferência auxiliar incompatível com o contrato.")
        return result

    def _read(self, identity: ResourceIdentity) -> ResourceRead:
        data: dict[str, object] = {"internal_id": identity.internal_id, "uri": identity.uri}

        def field(
            name: str, predicate: URIRef, convert: Callable[[Node], object], *, single: bool = False
        ) -> None:
            self.fields[name] = predicate
            values = self.objects(self.root, predicate)
            data[name] = (
                convert(self.one(values)) if single else self.values(self.root, predicate, convert)
            )

        def auxiliary(name: str, predicate: URIRef) -> None:
            field(name, predicate, lambda value: self.auxiliary(value, name))

        def relation(name: str, entity: EntityType, *, single: bool = False) -> None:
            definitions = [
                d
                for d in DEFAULT_REGISTRY.entries.values()
                if d.source == entity and d.field == name and not d.derived
            ]
            if len(definitions) != 1:
                raise RdfDocumentError("Campo sem relação autorizada.")
            definition = definitions[0]
            predicate = URIRef(definition.predicate)
            if not definition.self_allowed and (self.root, predicate, self.root) in self.graph:
                raise RdfDocumentError("Autorreferência incompatível com o contrato.")
            field(name, predicate, self.reference, single=single)

        if self.kind in (BF.Work, BF.Instance):
            auxiliary("title", BF.title)
        if self.kind in (BF.Work, BF.Instance, BF.Item):
            auxiliary("note", BF.note)
        if self.kind in (BF.Instance, BF.Item, BF.Agent, BF.Person, BF.Organization):
            auxiliary("identified_by", BF.identifiedBy)
        model: type[ResourceRead]
        if self.kind == BF.Work:
            model = WorkRead
            field("language", BF.language, self.reference)
            field("content", BF.content, self.reference)
            for name in ("subject", "related_to", "translation_of"):
                relation(name, EntityType.WORK)
            auxiliary("contribution", BF.contribution)
            auxiliary("classification", BF.classification)
        elif self.kind == BF.Instance:
            model = InstanceRead
            relation("instance_of", EntityType.INSTANCE, single=True)
            field("edition_statement", BF.editionStatement, self.text)
            field("carrier", BF.carrier, self.reference)
            auxiliary("provision_activity", BF.provisionActivity)
            auxiliary("extent", BF.extent)
        elif self.kind == BF.Item:
            model = ItemRead
            relation("item_of", EntityType.ITEM, single=True)
            relation("held_by", EntityType.ITEM)
            field("custodial_history", BF.custodialHistory, self.text)
            auxiliary("shelf_mark", BF.shelfMark)
        elif self.kind in (BF.Agent, BF.Person, BF.Organization):
            model = AgentRead
            data["kind"] = str(self.kind).removeprefix(str(BF))
            field("authorized_name", RDFS.label, self.text)
            field("variant_name", SKOS.altLabel, self.text)
            relation("related_authority", EntityType.AGENT)
        else:
            model = SubjectRead
            field("preferred_label", SKOS.prefLabel, self.text)
            field("alternative_label", SKOS.altLabel, self.text)
            field("scheme", SKOS.inScheme, self.reference)
            relation("broader", EntityType.SUBJECT)
            relation("related", EntityType.SUBJECT)
        if model in (AgentRead, SubjectRead):
            field("external_reference", RDFS.seeAlso, self.reference)
        if model in (ItemRead, AgentRead, SubjectRead):
            field("provenance", PROV.wasDerivedFrom, self.reference)
        return model.model_validate(data)


def graph_to_read(graph: Graph, identity: ResourceIdentity) -> ResourceRead:
    """Identity is caller-owned storage metadata, never inferred from an RDF IRI."""
    return GraphProjection(graph, identity).resource
