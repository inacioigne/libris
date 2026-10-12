"""Explicit catalog-value → RDF mapping; enrichments never describe external targets."""

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF, SKOS

from libris.modules.bibliographic.application.controlled_values import (
    CatalogValue,
    EntityValue,
    LiteralValue,
    LocalConcept,
    parse_catalog_value,
)
from libris.modules.bibliographic.domain.iris import validate_iri
from libris.modules.bibliographic.infrastructure.rdf import check_graph, new_graph

from .mapping import ReferenceMapping, reference_to_uri


def catalog_value_to_graph(
    subject: str,
    predicate: str,
    value: CatalogValue,
    *,
    references: ReferenceMapping | None = None,
) -> Graph:
    """One assertion only; caller supplies a profile-approved property and stored subject."""
    value = parse_catalog_value(value.model_dump())
    graph = new_graph()
    term: Literal | URIRef
    if isinstance(value, LiteralValue):
        term = Literal(
            value.value,
            lang=value.language,
            datatype=URIRef(value.datatype) if value.datatype else None,
            normalize=False,
        )
    elif isinstance(value, EntityValue):
        term = reference_to_uri(value.reference, references=references)
    else:
        term = URIRef(value.uri)
    graph.add((URIRef(validate_iri(subject)), URIRef(validate_iri(predicate)), term))
    check_graph(graph)
    return graph


def local_concept_to_graph(concept: LocalConcept) -> Graph:
    """Owned local SKOS description, deliberately separate from a bibliographic link."""
    concept = LocalConcept.model_validate(concept.model_dump())
    graph = new_graph()
    root = URIRef(concept.uri)
    graph.add((root, RDF.type, SKOS.Concept))
    graph.add((root, SKOS.inScheme, URIRef(concept.vocabulary)))
    for predicate, texts in (
        (SKOS.prefLabel, concept.label),
        (SKOS.altLabel, concept.alternative_labels),
    ):
        for text in texts:
            graph.add((root, predicate, Literal(text.value, lang=text.language)))
    if concept.notation is not None:
        graph.add((root, SKOS.notation, Literal(concept.notation)))
    # Source/status/replacement concern resolution; no implicit RDF equivalence or assertion.
    check_graph(graph)
    return graph
