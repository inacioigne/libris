import json
from typing import Literal as Format
from urllib.parse import urlsplit

from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.compare import isomorphic
from rdflib.namespace import DCTERMS, PROV, RDF, SKOS

from libris.core.config import Settings

BF = Namespace("http://id.loc.gov/ontologies/bibframe/")
RdfFormat = Format["json-ld", "turtle"]


class RdfDocumentError(ValueError):
    """Invalid or unsupported RDF input/conversion."""


def new_graph() -> Graph:
    graph = Graph()
    for prefix, namespace in [("bf", BF), ("dcterms", DCTERMS), ("skos", SKOS), ("prov", PROV)]:
        graph.bind(prefix, namespace)
    return graph


def _check_json(value: object, depth: int = 0, in_context: bool = False) -> None:
    if depth > 64:
        raise RdfDocumentError("JSON-LD excede a profundidade permitida.")
    if isinstance(value, dict):
        if "@import" in value or "@reverse" in value:
            raise RdfDocumentError("@import e @reverse não são suportados neste protótipo.")
        if "@graph" in value:
            raise RdfDocumentError("Named graphs exigem um Dataset; este núcleo aceita um grafo.")
        context = value.get("@context")
        if context is not None and not isinstance(context, dict):
            raise RdfDocumentError("Contextos devem ser objetos locais, sem URLs ou listas.")
        for key, child in value.items():
            _check_json(child, depth + 1, in_context or key == "@context")
    elif (
        in_context
        and isinstance(value, str)
        and value in {"@context", "@graph", "@import", "@reverse"}
    ):
        raise RdfDocumentError("Aliases de palavras reservadas não são suportados.")
    elif isinstance(value, list):
        for child in value:
            _check_json(child, depth + 1, in_context)


def check_graph(graph: Graph) -> None:
    for subject, predicate, value in graph:
        if not isinstance(subject, (URIRef, BNode)) or not isinstance(predicate, URIRef):
            raise RdfDocumentError("Sujeito ou predicado RDF inválido.")
        if not isinstance(value, (URIRef, BNode, Literal)):
            raise RdfDocumentError("Objeto RDF inválido.")
        for term in (subject, predicate, value):
            if isinstance(term, URIRef) and not urlsplit(str(term)).scheme:
                raise RdfDocumentError("IRIs relativas não são aceitas.")
        if isinstance(value, Literal) and value.ill_typed:
            raise RdfDocumentError("Literal incompatível com seu datatype RDF.")


def parse_document(document: str, format: RdfFormat, limit: int | None = None) -> Graph:
    if format not in ("json-ld", "turtle"):
        raise RdfDocumentError("Formato RDF não suportado.")
    effective_limit = Settings().rdf_max_document_bytes if limit is None else limit
    if len(document.encode("utf-8")) > effective_limit:
        raise RdfDocumentError("Documento RDF excede o limite de bytes.")
    try:
        if format == "json-ld":
            _check_json(json.loads(document))
        graph = new_graph().parse(data=document, format=format, publicID="urn:libris:input:")
        check_graph(graph)
        return graph
    except RdfDocumentError:
        raise
    except Exception as exc:
        raise RdfDocumentError("Não foi possível interpretar o documento RDF.") from exc


def serialize_document(graph: Graph, format: RdfFormat) -> str:
    if format not in ("json-ld", "turtle"):
        raise RdfDocumentError("Formato RDF não suportado.")
    check_graph(graph)
    try:
        document = graph.serialize(format=format)
        recovered = parse_document(document, format)
        if not isomorphic(graph, recovered):
            raise RdfDocumentError("Conversão RDF alterou a semântica do grafo.")
        return document
    except RdfDocumentError:
        raise
    except Exception as exc:
        raise RdfDocumentError("Não foi possível serializar o grafo RDF.") from exc


def add_resource(graph: Graph, uri: str, rdf_class: URIRef) -> URIRef:
    node = URIRef(uri)
    graph.add((node, RDF.type, rdf_class))
    return node


def link_instance(graph: Graph, instance: URIRef, work: URIRef) -> None:
    graph.add((instance, BF.instanceOf, work))
    graph.add((work, BF.hasInstance, instance))


def link_item(graph: Graph, item: URIRef, instance: URIRef) -> None:
    graph.add((item, BF.itemOf, instance))
    graph.add((instance, BF.hasItem, item))
