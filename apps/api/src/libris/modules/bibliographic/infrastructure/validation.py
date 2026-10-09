from dataclasses import dataclass
from importlib.resources import files

from pyshacl import validate
from rdflib import Graph
from rdflib.namespace import RDF, SH

from libris.modules.bibliographic.infrastructure.rdf import check_graph

PROFILE_ID = "urn:libris:profile:monograph:v1"


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
    check_graph(graph)
    shapes = Graph().parse(
        data=files("libris.modules.bibliographic")
        .joinpath("resources/monograph-v1.ttl")
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
