"""Pure RDF graph comparison; blank node labels are local canonical descriptions."""

from dataclasses import dataclass
from typing import Literal as LiteralType

from rdflib import BNode, Graph, Literal, URIRef
from rdflib.compare import graph_diff, to_isomorphic
from rdflib.term import Node

TermKind = LiteralType["iri", "blank_node", "literal"]


@dataclass(frozen=True)
class RdfTerm:
    kind: TermKind
    value: str
    language: str | None = None
    datatype: str | None = None


@dataclass(frozen=True)
class RdfStatement:
    subject: RdfTerm
    predicate: RdfTerm
    object: RdfTerm


@dataclass(frozen=True)
class SemanticDiff:
    added: tuple[RdfStatement, ...]
    removed: tuple[RdfStatement, ...]

    @property
    def is_empty(self) -> bool:
        return not self.added and not self.removed


def _term(term: Node) -> RdfTerm:
    if isinstance(term, URIRef):
        return RdfTerm("iri", str(term))
    if isinstance(term, BNode):
        return RdfTerm("blank_node", str(term))
    if isinstance(term, Literal):
        return RdfTerm(
            "literal",
            str(term),
            term.language,
            str(term.datatype) if term.datatype is not None else None,
        )
    raise ValueError("Termo não pertence ao contrato RDF.")


def _statements(graph: Graph) -> tuple[RdfStatement, ...]:
    triples = sorted(graph, key=lambda triple: tuple(term.n3() for term in triple))
    return tuple(RdfStatement(_term(s), _term(p), _term(o)) for s, p, o in triples)


def compare_graphs(previous: Graph, current: Graph) -> SemanticDiff:
    """Canonicalize each whole graph using rdflib.compare, with no remote resolution.

    Structural changes can relabel an entire blank-node component and report its
    surrounding statements too. This is a graph delta, not a minimal edit script
    or a claim of persistent identity for blank nodes. Inputs are never mutated.
    """
    if previous.context_aware or current.context_aware:
        raise ValueError("Comparação exige Graph simples, sem datasets.")
    _, removed, added = graph_diff(to_isomorphic(previous), to_isomorphic(current))
    return SemanticDiff(_statements(added), _statements(removed))
