"""Represent Graph directly; DTO conversion is a separate, deliberately partial surface."""

import json
from collections.abc import Iterable
from hashlib import sha256
from importlib.resources import files

from rdflib import BNode, Graph, URIRef
from rdflib.compare import isomorphic

from libris.core.config import Settings
from libris.modules.bibliographic.domain.iris import validate_iri
from libris.modules.bibliographic.domain.models import validate_identity_uri
from libris.modules.bibliographic.infrastructure.ownership import check_snapshot, compose_snapshots
from libris.modules.bibliographic.infrastructure.rdf import (
    RdfDocumentError,
    RdfFormat,
    check_graph,
    new_graph,
    parse_document,
    serialize_document,
)

from .mapping import ReferenceMapping, ResourceRead, resource_to_graph

CONTRACT_VERSION = "1.0"
CONTEXT_VERSION = "bibframe-v1"
SemanticFormat = RdfFormat


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise RdfDocumentError("Propriedade JSON-LD duplicada.")
        result[key] = value
    return result


def local_context() -> dict[str, object]:
    """Return a fresh trusted context; do not accept a path or a context from clients."""
    document: object = json.loads(
        files("libris.modules.bibliographic")
        .joinpath("resources/contexts/bibframe-v1.jsonld")
        .read_text(encoding="utf-8")
    )
    if not isinstance(document, dict) or not isinstance(document.get("@context"), dict):
        raise RdfDocumentError("Artefato de contexto local inválido.")
    return dict(document["@context"])


def context_digest() -> str:
    """Canonical JSON SHA-256 for release verification, independent of indentation."""
    return sha256(
        json.dumps(
            local_context(), sort_keys=True, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()


def _check_depth(graph: Graph) -> None:
    # Only private structures are traversed, never descriptions of referenced entities.
    edges: dict[URIRef | BNode, set[URIRef | BNode]] = {}
    subjects = set(graph.subjects())
    for subject, _, value in graph:
        if isinstance(subject, (URIRef, BNode)) and (
            isinstance(value, BNode)
            or (isinstance(value, URIRef) and "#" in str(value) and value in subjects)
        ):
            assert isinstance(value, (URIRef, BNode))
            edges.setdefault(subject, set()).add(value)
    done: dict[URIRef | BNode, int] = {}
    active: set[URIRef | BNode] = set()

    def height(node: URIRef | BNode, depth: int) -> int:
        if depth > 64:
            raise RdfDocumentError("Grafo excede a profundidade auxiliar permitida.")
        if node in active:
            return 0  # RDF cycles are valid; no recursive expansion is performed.
        if node in done:
            return done[node]
        active.add(node)
        result = 1 + max((height(child, depth + 1) for child in edges.get(node, ())), default=0)
        active.remove(node)
        if result > 65:
            raise RdfDocumentError("Grafo excede a profundidade auxiliar permitida.")
        done[node] = result
        return result

    for node in edges:
        height(node, 0)


def _aliases(context: dict[str, object]) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for name, definition in context.items():
        if name.startswith("@"):
            continue
        iri = definition.get("@id") if isinstance(definition, dict) else definition
        if isinstance(iri, str) and ":" in iri:
            prefix, _, suffix = iri.partition(":")
            namespace = context.get(prefix)
            if isinstance(namespace, str):
                aliases[namespace + suffix] = name
    return aliases


def parse_representation(
    document: str, format: SemanticFormat, *, limit: int | None = None
) -> Graph:
    """Safe parser plus release-context policy; legacy parse_document remains compatible."""
    effective_limit = Settings().rdf_max_document_bytes if limit is None else limit
    if len(document.encode("utf-8")) > effective_limit:
        raise RdfDocumentError("Documento RDF excede o limite de bytes.")
    if format == "json-ld":
        try:
            value: object = json.loads(document, object_pairs_hook=_unique_object)
        except (ValueError, RecursionError) as error:
            raise RdfDocumentError("JSON-LD inválido.") from error
        context = local_context()
        if not isinstance(value, (dict, list)) or (
            isinstance(value, list) and not all(isinstance(node, dict) for node in value)
        ):
            raise RdfDocumentError("JSON-LD exige objeto ou array de nós.")

        def inspect(node: object, depth: int = 0, scoped: bool = False) -> None:
            if depth > 64:
                raise RdfDocumentError("JSON-LD excede a profundidade permitida.")
            if isinstance(node, dict):
                if "@context" in node:
                    if node["@context"] != context:
                        raise RdfDocumentError("Contexto não autorizado para esta release.")
                    scoped = True
                for key, child in node.items():
                    if key == "@context":
                        continue
                    if key.startswith("@"):
                        if key not in {"@id", "@type", "@value", "@language", "@list"}:
                            raise RdfDocumentError("Palavra reservada JSON-LD não suportada.")
                    elif key in context and not scoped:
                        raise RdfDocumentError("Termo compacto exige o contexto local da release.")
                    elif key not in context:
                        try:
                            validate_iri(key)
                        except ValueError as error:
                            raise RdfDocumentError(
                                "Termo desconhecido sem IRI explícita."
                            ) from error
                    if key in {"@id", "@type"}:
                        terms = child if isinstance(child, list) else [child]
                        if key == "@id" and isinstance(child, list):
                            raise RdfDocumentError("@id exige uma única IRI ou blank node.")
                        for term in terms:
                            if not isinstance(term, str):
                                raise RdfDocumentError("Identificador/tipo JSON-LD inválido.")
                            if term.startswith("_:") and key == "@id" and len(term) > 2:
                                continue
                            try:
                                validate_iri(term)
                            except ValueError as error:
                                raise RdfDocumentError(
                                    "Identificador/tipo JSON-LD inválido."
                                ) from error
                    if key == "@value" and not isinstance(child, (str, int, float, bool)):
                        raise RdfDocumentError("Objeto literal JSON-LD incompatível.")
                    if key != "@value":
                        inspect(child, depth + 1, scoped)
            elif isinstance(node, list):
                for child in node:
                    inspect(child, depth + 1, scoped)

        inspect(value)
    graph = parse_document(document, format, limit=effective_limit)
    _check_depth(graph)
    return graph


def serialize_graph(graph: Graph, *, format: SemanticFormat, root: str | None = None) -> str:
    """Integral Graph export. root enforces owned-snapshot rules when supplied."""
    check_graph(graph)
    if root is not None:
        check_snapshot(graph, URIRef(validate_identity_uri(root)))
    _check_depth(graph)
    # Serializers may bind prefixes on the graph's namespace manager. Work on a copy.
    original = graph
    graph = new_graph()
    for prefix, namespace in original.namespaces():
        graph.bind(prefix, namespace)
    for triple in original:
        graph.add(triple)
    document = serialize_document(graph, format)
    if format == "json-ld":
        # Limited compaction: shorten known top-level predicates only. Preserve value
        # objects, datatypes, @id and @type verbatim; never ask RDFLib to emit @graph.
        expanded: object = json.loads(document)
        if not isinstance(expanded, list) or not all(isinstance(node, dict) for node in expanded):
            raise RdfDocumentError("A representação expandida deve ser uma lista de nós.")
        context = local_context()
        aliases = _aliases(context)
        compact = [
            {"@context": context, **{aliases.get(key, key): value for key, value in node.items()}}
            for node in expanded
        ]
        document = json.dumps(compact, ensure_ascii=False, indent=2)
    recovered = parse_representation(document, format)
    if not isomorphic(graph, recovered):
        raise RdfDocumentError("Compactação alterou a semântica do grafo.")
    return document


def serialize_resource(
    resource: ResourceRead, *, format: SemanticFormat, references: ReferenceMapping | None = None
) -> str:
    return serialize_graph(
        resource_to_graph(resource, references=references), format=format, root=resource.uri
    )


def serialize_composed(snapshots: Iterable[tuple[URIRef, Graph]], *, format: SemanticFormat) -> str:
    """Explicit caller-selected snapshots; existing composition adds only its inverses."""
    return serialize_graph(compose_snapshots(snapshots), format=format)
