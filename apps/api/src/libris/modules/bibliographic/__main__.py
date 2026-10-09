"""Local RDF inspection/export; no HTTP or database writes."""

import argparse
import json
from pathlib import Path

from libris.core.config import Settings
from libris.modules.bibliographic.infrastructure.rdf import parse_document, serialize_document
from libris.modules.bibliographic.infrastructure.validation import (
    PROFILE_ID,
    PROFILE_SHAPES,
    validate_profile,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Valida e exporta um grafo bibliográfico local.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--format", choices=("turtle", "json-ld"), default="turtle")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--profile", choices=tuple(PROFILE_SHAPES), default=PROFILE_ID)
    parser.add_argument("--composed", action="store_true")
    args = parser.parse_args()
    settings = Settings()
    with args.input.open("rb") as source:
        document = source.read(settings.rdf_max_document_bytes + 1)
    graph = parse_document(document.decode("utf-8"), args.format)
    report = validate_profile(graph, args.profile, composed=args.composed)
    print(
        json.dumps(
            {
                "profile": args.profile,
                "conforms": report.conforms,
                "triples": len(graph),
                "issues": [
                    {
                        "focusNode": issue.focus_node,
                        "path": issue.path,
                        "severity": issue.severity,
                        "messages": issue.messages,
                    }
                    for issue in report.issues
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / "book.jsonld").write_text(
            serialize_document(graph, "json-ld"), encoding="utf-8"
        )
        (args.output_dir / "book.ttl").write_text(
            serialize_document(graph, "turtle"), encoding="utf-8"
        )
    if not report.conforms:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
