"""Adapt existing reports, preserving RDF identities without exposing RDF objects."""

from functools import lru_cache
from hashlib import sha256
from importlib.resources import files
from typing import Literal as ContextLiteral
from urllib.parse import urlsplit

from rdflib import BNode, Graph, Literal, URIRef
from rdflib.compare import to_canonical_graph
from rdflib.namespace import RDF, SH
from rdflib.plugins.parsers.notation3 import BadSyntax
from rdflib.term import Node

from libris.core.correlation import request_id_context
from libris.modules.bibliographic.application.diagnostics import (
    CatalogValidationResult,
    Diagnostic,
    RdfPath,
    Severity,
)
from libris.modules.bibliographic.domain.errors import CatalogCode
from libris.modules.bibliographic.domain.profile_contract import ResolvedProfile
from libris.modules.bibliographic.domain.profiles import CatalogProfile
from libris.modules.bibliographic.infrastructure.validation import (
    SHAPE_RELEASE_FILES,
    FieldValidationIssue,
    ValidationIssue,
    ValidationReport,
    correlate_validation_issues,
)

COMPONENT_CODES = {
    str(SH.MinCountConstraintComponent): CatalogCode.MIN_COUNT,
    str(SH.MaxCountConstraintComponent): CatalogCode.MAX_COUNT,
    str(SH.QualifiedMinCountConstraintComponent): CatalogCode.QUALIFIED_MIN_COUNT,
    str(SH.QualifiedMaxCountConstraintComponent): CatalogCode.QUALIFIED_MAX_COUNT,
    str(SH.DatatypeConstraintComponent): CatalogCode.DATATYPE,
    str(SH.NodeKindConstraintComponent): CatalogCode.NODE_KIND,
    str(SH.ClassConstraintComponent): CatalogCode.CLASS,
    str(SH.InConstraintComponent): CatalogCode.IN,
}
MESSAGES = {
    CatalogCode.MIN_COUNT: "Quantidade mínima de valores não satisfeita.",
    CatalogCode.MAX_COUNT: "Quantidade máxima de valores excedida.",
    CatalogCode.QUALIFIED_MIN_COUNT: "Quantidade mínima de valores qualificados não satisfeita.",
    CatalogCode.QUALIFIED_MAX_COUNT: "Quantidade máxima de valores qualificados excedida.",
    CatalogCode.DATATYPE: "Valor incompatível com o datatype esperado.",
    CatalogCode.NODE_KIND: "Tipo de nó RDF incompatível.",
    CatalogCode.CLASS: "Classe RDF incompatível.",
    CatalogCode.IN: "Valor fora do conjunto permitido.",
    CatalogCode.SHACL: "Inconsistência semântica detectada.",
}


def safe_iri(value: str | None) -> str | None:
    """Preserve full ontology IRIs; omit credentials, queries, files and oversize IRIs."""
    if value is None or len(value) > 2048 or any(ord(char) < 33 for char in value):
        return None
    try:
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https", "urn"}:
            return None
        if parsed.username or parsed.password or parsed.query:
            return None
    except ValueError:
        return None
    return value


@lru_cache(maxsize=1)
def trusted_messages() -> frozenset[str]:
    """Only fixed package-authored messages are safe; engine messages can echo input."""
    messages: set[str] = set()
    names = {name for group in SHAPE_RELEASE_FILES.values() for name in group}
    for name in sorted(names):
        source = files("libris.modules.bibliographic").joinpath("resources", name)
        try:
            graph = Graph().parse(data=source.read_text("utf-8"), format="turtle")
        except (OSError, BadSyntax):
            # Optional message metadata must not fail a successfully executed validation.
            continue
        messages.update(str(message) for message in graph.objects(None, SH.message))
    return frozenset(messages)


class ReportTerms:
    def __init__(self, graph: Graph) -> None:
        self.graph = graph
        self.identifiers: dict[Node, str] = {}

    def identifier(self, term: Node | None, fallback: str | None = None) -> str | None:
        if isinstance(term, URIRef):
            return safe_iri(str(term))
        if isinstance(term, BNode):
            if term not in self.identifiers:
                # Rooted reachable description: stable under blank-node renaming.
                rooted = Graph()
                rooted.add((URIRef("urn:libris:diagnostic:root"), RDF.value, term))
                if not any(self.graph.triples((term, None, None))):
                    # Anonymous source shapes may only have incoming report references.
                    for subject, predicate in self.graph.subject_predicates(term):
                        if isinstance(subject, BNode):
                            for triple in self.graph.triples((subject, None, None)):
                                rooted.add(triple)
                pending: list[Node] = [term]
                seen: set[Node] = set()
                while pending:
                    subject = pending.pop()
                    if subject in seen:
                        continue
                    seen.add(subject)
                    for triple in self.graph.triples((subject, None, None)):
                        rooted.add(triple)
                        if isinstance(triple[2], BNode):
                            pending.append(triple[2])
                redacted = Graph()
                for subject, predicate, value in rooted:
                    redacted.add(
                        (
                            subject,
                            predicate,
                            URIRef("urn:libris:diagnostic:literal")
                            if isinstance(value, Literal)
                            else value,
                        )
                    )
                canonical = to_canonical_graph(redacted)
                content = "\n".join(sorted(f"{s.n3()} {p.n3()} {o.n3()}" for s, p, o in canonical))
                self.identifiers[term] = "_:sha256-" + sha256(content.encode()).hexdigest()
            return self.identifiers[term]
        return safe_iri(fallback)

    def path(self, term: Node | None, fallback: str | None, depth: int = 0) -> RdfPath | None:
        if term is None:
            iri = safe_iri(fallback)
            return RdfPath(kind="iri", iri=iri) if iri else None
        if isinstance(term, URIRef):
            iri = safe_iri(str(term))
            return RdfPath(kind="iri", iri=iri) if iri else None
        if not isinstance(term, BNode):
            return None
        opaque = RdfPath(kind="opaque", identifier=self.identifier(term))
        if depth >= 16:
            return opaque
        if (term, RDF.first, None) in self.graph:
            items: list[RdfPath] = []
            visited: set[Node] = set()
            cursor: Node | None = term
            while cursor is not None and cursor != RDF.nil:
                if cursor in visited or len(items) >= 64:
                    return opaque
                visited.add(cursor)
                item = self.path(self.graph.value(cursor, RDF.first), None, depth + 1)
                if item is None:
                    return opaque
                items.append(item)
                cursor = self.graph.value(cursor, RDF.rest)
            return RdfPath(kind="sequence", items=tuple(items)) if cursor == RDF.nil else opaque
        for predicate, kind in (
            (SH.inversePath, "inverse"),
            (SH.zeroOrMorePath, "zero_or_more"),
            (SH.oneOrMorePath, "one_or_more"),
            (SH.zeroOrOnePath, "zero_or_one"),
        ):
            child = self.graph.value(term, predicate)
            if child is not None:
                item = self.path(child, None, depth + 1)
                if item is not None:
                    return RdfPath(kind=kind, items=(item,))
        alternative = self.graph.value(term, SH.alternativePath)
        if alternative is not None:
            sequence = self.path(alternative, None, depth + 1)
            if sequence is not None and sequence.kind == "sequence":
                return RdfPath(kind="alternative", items=sequence.items)
        return opaque


def legacy_fields(issue: ValidationIssue, profile: CatalogProfile, graph: Graph) -> tuple[str, ...]:
    if issue.path_term is not None and not isinstance(issue.path_term, URIRef):
        return ()
    focus = issue.focus_term
    if focus is None:
        matches = [node for node in graph.all_nodes() if str(node) == issue.focus_node]
        if len(matches) != 1:
            return ()
        focus = matches[0]
    classes = {str(kind) for kind in graph.objects(focus, RDF.type)}
    return tuple(
        sorted(
            {
                f"{resource.rdf_class}/{field.name}"
                for resource in profile.resources
                if resource.rdf_class in classes
                for field in resource.fields
                if field.property == issue.path
            }
        )
    )


def adapt_report(
    report: ValidationReport,
    profile: CatalogProfile | ResolvedProfile,
    graph: Graph,
    *,
    context: ContextLiteral["snapshot", "composed"] = "snapshot",
    request_id: str | None = None,
) -> CatalogValidationResult:
    terms = ReportTerms(report.graph + graph)
    mapped = (
        correlate_validation_issues(report, profile, graph)
        if isinstance(profile, ResolvedProfile)
        else tuple(
            FieldValidationIssue(issue, legacy_fields(issue, profile, graph))
            for issue in report.issues
        )
    )
    diagnostics: list[Diagnostic] = []
    severities: dict[str, Severity] = {
        str(SH.Violation): "Violation",
        str(SH.Warning): "Warning",
        str(SH.Info): "Info",
    }
    for entry in mapped:
        issue = entry.issue
        code = COMPONENT_CODES.get(issue.source_constraint_component or "", CatalogCode.SHACL)
        severity = severities.get(issue.severity, "Violation")
        diagnostics.append(
            Diagnostic(
                code=code,
                message=MESSAGES[code],
                category="semantic",
                severity=severity,
                field_ids=entry.field_ids,
                path=terms.path(issue.path_term, issue.path),
                focus_node=terms.identifier(issue.focus_term, issue.focus_node),
                # Literal values always omitted; safe URI values keep their exact identity.
                value=safe_iri(str(issue.value_term))
                if isinstance(issue.value_term, URIRef)
                else None,
                constraint=safe_iri(issue.source_constraint_component),
                source_shape=terms.identifier(issue.source_shape_term, issue.source_shape),
                messages=tuple(
                    message for message in issue.messages if message in trusted_messages()
                ),
                parameters={"component": issue.source_constraint_component}
                if issue.source_constraint_component in COMPONENT_CODES
                else {},
            )
        )
    return CatalogValidationResult(
        state="completed",
        conforms=report.conforms
        and not any(issue.severity == "Violation" for issue in diagnostics),
        profile_id=profile.id,
        profile_release=profile.release_id if isinstance(profile, ResolvedProfile) else profile.id,
        profile_version=profile.release,
        context=context,
        request_id=request_id_context.get() or request_id,
        issues=tuple(diagnostics),
    )
