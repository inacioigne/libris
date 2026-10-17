"""Operações pontuais sobre snapshots integrais, sem reconstrução por Read."""

from rdflib import BNode, Graph, URIRef
from rdflib.compare import to_canonical_graph
from rdflib.namespace import RDF
from rdflib.term import IdentifiedNode

from libris.modules.bibliographic.api.schemas.common import UnreconciledReference
from libris.modules.bibliographic.api.schemas.relationships import (
    ContributionLink,
    Link,
    PublicationLink,
    RelationshipCreate,
    same_link,
)
from libris.modules.bibliographic.domain.errors import CatalogCode, CatalogError
from libris.modules.bibliographic.infrastructure.rdf import BF, new_graph


def canonical_snapshot(graph: Graph) -> Graph:
    result = new_graph()
    for prefix, namespace in graph.namespaces():
        result.bind(prefix, namespace)
    for triple in to_canonical_graph(graph):
        result.add(triple)
    return result


def target_uri(link: Link) -> URIRef:
    if isinstance(link.target, UnreconciledReference) or link.target.uri is None:
        raise CatalogError(CatalogCode.REFERENCE_INVALID, "Referência exige URI resolvida.")
    return URIRef(link.target.uri)


def auxiliary(graph: Graph, root: URIRef, link: Link) -> IdentifiedNode | None:
    if isinstance(link, PublicationLink):
        return next(
            (
                node
                for node in graph.objects(root, BF.provisionActivity)
                if isinstance(node, (BNode, URIRef)) and str(node) == link.activity_key
            ),
            None,
        )
    if isinstance(link, ContributionLink):
        return next(
            (
                node
                for node in graph.objects(root, BF.contribution)
                if isinstance(node, (BNode, URIRef))
                and (node, BF.agent, target_uri(link)) in graph
                and {str(role) for role in graph.objects(node, BF.role)} == set(link.role)
            ),
            None,
        )
    return None


def change_relationship_graph(
    graph: Graph, before: RelationshipCreate, after: RelationshipCreate
) -> Graph:
    """Preserva nós retidos; publicação perde somente a aresta de agente pedida."""
    result = new_graph()
    for prefix, namespace in graph.namespaces():
        result.bind(prefix, namespace)
    for triple in graph:
        result.add(triple)
    root = URIRef(str(before.source.uri))
    for link in before.links:
        if any(same_link(link, retained) for retained in after.links):
            continue
        node = auxiliary(graph, root, link)
        if isinstance(link, PublicationLink):
            if node is None:
                raise CatalogError(CatalogCode.REFERENCE_INVALID, "Publicação inexistente.")
            result.remove((node, BF.agent, target_uri(link)))
        elif isinstance(link, ContributionLink):
            if node is None:
                raise CatalogError(CatalogCode.REFERENCE_INVALID, "Contribuição inexistente.")
            allowed = {(node, RDF.type, BF.Contribution), (node, BF.agent, target_uri(link))}
            allowed.update((node, BF.role, URIRef(role)) for role in link.role)
            if set(graph.triples((node, None, None))) != allowed or set(
                graph.triples((None, None, node))
            ) != {(root, BF.contribution, node)}:
                raise CatalogError(CatalogCode.PROFILE_POLICY, "Remoção perderia anotações.")
            result.remove((root, BF.contribution, node))
            result.remove((node, None, None))
        else:
            result.remove((root, URIRef(link.predicate), target_uri(link)))
    publications: dict[str, IdentifiedNode] = {}
    for link in after.links:
        if any(same_link(link, retained) for retained in before.links):
            continue
        if isinstance(link, PublicationLink):
            node = auxiliary(graph, root, link) or publications.setdefault(
                link.activity_key, BNode()
            )
            result.add((root, BF.provisionActivity, node))
            result.add((node, RDF.type, BF.Publication))
            result.add((node, BF.agent, target_uri(link)))
        elif isinstance(link, ContributionLink):
            node = BNode()
            result.add((root, BF.contribution, node))
            result.add((node, RDF.type, BF.Contribution))
            result.add((node, BF.agent, target_uri(link)))
            for role in link.role:
                result.add((node, BF.role, URIRef(role)))
        else:
            result.add((root, URIRef(link.predicate), target_uri(link)))
    return result
