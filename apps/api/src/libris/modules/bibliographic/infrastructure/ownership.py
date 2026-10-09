"""Entity-owned RDF snapshots and explicitly derived inverse relationships."""

from collections.abc import Iterable

from rdflib import BNode, Graph, URIRef
from rdflib.namespace import RDF, SKOS

from libris.modules.bibliographic.infrastructure.rdf import BF, check_graph, new_graph

ENTITY_TYPES = (BF.Work, BF.Instance, BF.Item, BF.Agent, BF.Person, BF.Organization, SKOS.Concept)
INVERSES = {BF.instanceOf: BF.hasInstance, BF.itemOf: BF.hasItem}


def entity_kind(graph: Graph, root: URIRef) -> URIRef:
    kinds = {kind for kind in ENTITY_TYPES if (root, RDF.type, kind) in graph}
    if BF.Person in kinds or BF.Organization in kinds:
        kinds.discard(BF.Agent)
    if len(kinds) != 1:
        raise ValueError("A URI raiz deve ter exatamente um tipo de entidade suportado.")
    return kinds.pop()


def owned_nodes(graph: Graph, root: URIRef) -> set[URIRef | BNode]:
    """Follow private nodes only; another persistent entity is always a boundary."""
    nodes: set[URIRef | BNode] = {root}
    pending: list[URIRef | BNode] = [root]
    while pending:
        subject = pending.pop()
        for value in graph.objects(subject):
            if not isinstance(value, (URIRef, BNode)) or value in nodes:
                continue
            if isinstance(value, URIRef):
                # Auxiliary IRIs are scoped to the owner's identity. Other IRIs are references.
                if not str(value).startswith(f"{root}#"):
                    continue
            if any((value, RDF.type, kind) in graph for kind in ENTITY_TYPES):
                continue
            nodes.add(value)
            pending.append(value)
    return nodes


def check_snapshot(graph: Graph, root: URIRef) -> URIRef:
    check_graph(graph)
    kind = entity_kind(graph, root)
    nodes = owned_nodes(graph, root)
    if any(subject not in nodes for subject in graph.subjects()):
        raise ValueError("Snapshot contém descrição alheia ou nós sem proprietário.")
    if any(predicate in INVERSES.values() for predicate in graph.predicates()):
        raise ValueError("Relações inversas são derivadas, não gravadas no snapshot.")
    for node in nodes - {root}:
        if any((node, RDF.type, entity_type) in graph for entity_type in ENTITY_TYPES):
            raise ValueError("Entidades persistentes exigem snapshot independente.")
    return kind


def compose_snapshots(snapshots: Iterable[tuple[URIRef, Graph]]) -> Graph:
    """Compose canonical snapshots without sharing blank-node identities or mutations."""
    result = new_graph()
    seen: set[URIRef] = set()
    for root, graph in snapshots:
        check_snapshot(graph, root)
        if root in seen:
            raise ValueError("A composição não aceita duas revisões da mesma entidade.")
        seen.add(root)
        blanks: dict[BNode, BNode] = {}
        for subject, predicate, value in graph:
            if isinstance(subject, BNode):
                subject = blanks.setdefault(subject, BNode())
            if isinstance(value, BNode):
                value = blanks.setdefault(value, BNode())
            result.add((subject, predicate, value))
    for direct, inverse in INVERSES.items():
        for subject, value in list(result.subject_objects(direct)):
            result.add((value, inverse, subject))
    return result
