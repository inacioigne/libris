from dataclasses import dataclass
from importlib.resources import files

from pyshacl import validate
from rdflib import Graph, URIRef
from rdflib.namespace import RDF, SH

from libris.modules.bibliographic.domain.profile_contract import (
    ProfileValidationContext,
    ResolvedProfile,
)
from libris.modules.bibliographic.domain.profile_registry import ProfileError
from libris.modules.bibliographic.infrastructure.rdf import check_graph

PROFILE_ID = "urn:libris:profile:monograph:v1"
INSTITUTIONAL_PROFILE_ID = "urn:libris:profile:monograph:v1:1"
AUTHORITY_PROFILE_ID = "urn:libris:profile:authority:v1"
PROFILE_SHAPES = {
    PROFILE_ID: ("monograph-v1.ttl",),
    INSTITUTIONAL_PROFILE_ID: ("monograph-v1.1.ttl", "authority-v1.ttl"),
    AUTHORITY_PROFILE_ID: ("monograph-v1.1.ttl", "authority-v1.ttl"),
}


@dataclass(frozen=True)
class ValidationIssue:
    focus_node: str
    path: str | None
    severity: str
    messages: tuple[str, ...]


@dataclass(frozen=True)
class ValidationReport:
    conforms: bool
    issues: tuple[ValidationIssue, ...]
    graph: Graph


def validate_monograph(graph: Graph) -> ValidationReport:
    return validate_profile(graph, PROFILE_ID)


def validate_profile(graph: Graph, profile: str, *, composed: bool = False) -> ValidationReport:
    check_graph(graph)
    if profile not in PROFILE_SHAPES:
        raise ValueError("Perfil local desconhecido.")
    names = PROFILE_SHAPES[profile]
    if composed and profile != PROFILE_ID:
        names += ("monograph-v1.1-composed.ttl",)
    return _validate_shapes(graph, names)


def _validate_shapes(graph: Graph, names: tuple[str, ...]) -> ValidationReport:
    shapes = Graph()
    for name in names:
        shapes.parse(
            data=files("libris.modules.bibliographic")
            .joinpath(f"resources/{name}")
            .read_text(encoding="utf-8"),
            format="turtle",
        )
    conforms, report, _ = validate(
        graph,
        shacl_graph=shapes,
        inference="none",
        advanced=False,
        js=False,
        do_owl_imports=False,
        allow_warnings=True,
        allow_infos=True,
    )
    if not isinstance(report, Graph):
        raise ValueError("Falha na execução da validação SHACL.")
    issues = tuple(
        ValidationIssue(
            focus_node=str(report.value(result, SH.focusNode)),
            path=str(path) if (path := report.value(result, SH.resultPath)) else None,
            severity=str(report.value(result, SH.resultSeverity)),
            messages=tuple(str(message) for message in report.objects(result, SH.resultMessage)),
        )
        for result in report.subjects(RDF.type, SH.ValidationResult)
    )
    return ValidationReport(bool(conforms), issues, report)


# Package-owned mapping: configuration cannot choose paths, imports or URLs.
SHAPE_RELEASE_FILES = {
    ("urn:libris:shapes:institutional", "1.1", "snapshot"): (
        "monograph-v1.1.ttl",
        "authority-v1.ttl",
    ),
    ("urn:libris:shapes:institutional", "1.1", "composed"): (
        "monograph-v1.1.ttl",
        "authority-v1.ttl",
        "monograph-v1.1-composed.ttl",
    ),
    ("urn:libris:shapes:experimental", "1.0", "snapshot"): ("monograph-v1.ttl",),
}


@dataclass(frozen=True)
class FieldValidationIssue:
    issue: ValidationIssue
    field_ids: tuple[str, ...]


def validate_resolved_profile(
    graph: Graph, profile: ResolvedProfile, context: ProfileValidationContext
) -> ValidationReport:
    """Contract adapter only; all RDF validation still runs through existing pySHACL."""
    check_graph(graph)
    if context.profile_release != profile.release_id:
        raise ProfileError(
            "validation_release_mismatch", "Contexto e perfil usam releases distintas."
        )
    names: list[str] = []
    for reference in profile.validation:
        # A composed run applies snapshot rules too and adds local inverse checks.
        if context.mode == "snapshot" and reference.context != "snapshot":
            continue
        key = (reference.id, reference.release, context.mode)
        try:
            names.extend(SHAPE_RELEASE_FILES[key])
        except KeyError as error:
            raise ProfileError(
                "unknown_shapes", "Conjunto/contexto SHACL local não suportado."
            ) from error
    if not names:
        raise ProfileError("missing_shapes", "Nenhum conjunto SHACL aplicável ao contexto.")
    return _validate_shapes(graph, tuple(dict.fromkeys(names)))


def correlate_validation_issues(
    report: ValidationReport, profile: ResolvedProfile, graph: Graph
) -> tuple[FieldValidationIssue, ...]:
    """Unmapped/complex paths keep the original issue and an empty field list."""
    mapped: list[FieldValidationIssue] = []
    for issue in report.issues:
        focus = URIRef(issue.focus_node)
        # SHACL may focus auxiliary blank nodes as well as entity IRIs.
        nodes = [node for node in graph.all_nodes() if str(node) == issue.focus_node]
        classes = {str(kind) for node in nodes or [focus] for kind in graph.objects(node, RDF.type)}
        fields = tuple(
            sorted(
                {
                    field
                    for rdf_class in classes
                    for field in profile.fields_for_path(issue.path, rdf_class=rdf_class)
                }
            )
        )
        mapped.append(FieldValidationIssue(issue, fields))
    return tuple(mapped)
