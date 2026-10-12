"""Generate public examples from real fixtures/contracts, without HTTP/database writes."""

import argparse
import json
from http import HTTPStatus
from pathlib import Path

from pydantic import ValidationError
from rdflib import Graph, URIRef
from rdflib.namespace import RDF

from libris.api.problems import SAFE_DETAILS, ProblemDetails, adapt_pydantic_error, classify
from libris.modules.bibliographic.api.schemas import WorkCreate
from libris.modules.bibliographic.application.diagnostics import CatalogValidationResult, Diagnostic
from libris.modules.bibliographic.application.validation import validate_catalog
from libris.modules.bibliographic.domain.errors import CatalogCode
from libris.modules.bibliographic.domain.models import StaleRevisionError
from libris.modules.bibliographic.domain.profile_registry import ProfileError
from libris.modules.bibliographic.infrastructure.rdf import BF, parse_document
from libris.modules.bibliographic.infrastructure.validation import (
    INSTITUTIONAL_PROFILE_ID,
    PROFILE_ID,
    ShaclValidationError,
)

ROOT = Path(__file__).resolve().parents[1]
REQUEST_ID = "00000000-0000-4000-8000-000000000022"


def examples() -> dict[str, dict[str, object]]:
    graph = parse_document(
        (ROOT / "tests/fixtures/bibliographic/book.ttl").read_text(), "turtle", limit=1_048_576
    )
    good = validate_catalog(graph, PROFILE_ID, context="composed", request_id=REQUEST_ID)
    item = next(graph.subjects(RDF.type, BF.Item))
    graph.remove((item, BF.identifiedBy, None))
    warnings = validate_catalog(graph, PROFILE_ID, context="composed", request_id=REQUEST_ID)
    assert good.conforms and warnings.conforms
    assert any(issue.severity == "Warning" for issue in warnings.issues)
    invalid = Graph()
    invalid.add((URIRef("urn:example:work"), RDF.type, BF.Work))
    violations = validate_catalog(invalid, INSTITUTIONAL_PROFILE_ID, request_id=REQUEST_ID)
    assert violations.conforms is False
    result = {
        "conformant.json": good.public_dict(),
        "warnings.json": warnings.public_dict(),
        "violations.json": violations.public_dict(),
    }
    for name, error in (
        ("unknown-profile.json", ProfileError("unknown_profile", "untrusted text")),
        ("stale-revision.json", StaleRevisionError("untrusted text")),
        ("operational-failure.json", ShaclValidationError("shapes_unavailable", "untrusted text")),
    ):
        status, code = classify(error)
        result[name] = ProblemDetails(
            type=f"urn:libris:problem:v1:{code}",
            title=HTTPStatus(status).phrase,
            status=status,
            detail=SAFE_DETAILS[code],
            instance=f"urn:uuid:{REQUEST_ID}",
            code=code,
            request_id=REQUEST_ID,
        ).public_dict()
    try:
        WorkCreate.model_validate({})
    except ValidationError as error:
        result["schema-error.json"] = ProblemDetails(
            type="urn:libris:problem:v1:schema.invalid",
            title=HTTPStatus(422).phrase,
            status=422,
            detail=SAFE_DETAILS[CatalogCode.SCHEMA_INVALID],
            instance=f"urn:uuid:{REQUEST_ID}",
            code=CatalogCode.SCHEMA_INVALID,
            request_id=REQUEST_ID,
            issues=adapt_pydantic_error(error),
        ).public_dict()
    result["failed-validation.json"] = CatalogValidationResult(
        state="failed",
        profile_id=INSTITUTIONAL_PROFILE_ID,
        profile_release=INSTITUTIONAL_PROFILE_ID,
        profile_version="1.1",
        context="snapshot",
        request_id=REQUEST_ID,
        issues=(
            Diagnostic(
                code=CatalogCode.INFRASTRUCTURE_UNAVAILABLE,
                message="Validação indisponível.",
                category="technical",
            ),
        ),
    ).public_dict()
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    target = ROOT / "docs/examples/validation"
    for name, payload in examples().items():
        document = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        path = target / name
        if args.check:
            if not path.exists() or path.read_text() != document:
                raise SystemExit(f"Exemplo divergente: {name}")
        else:
            path.write_text(document)


if __name__ == "__main__":
    main()
