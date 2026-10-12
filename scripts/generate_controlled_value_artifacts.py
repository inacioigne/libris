"""Generate/check additive v1 schema and examples; never touches historical releases."""

import argparse
import json
from pathlib import Path

from libris.modules.bibliographic.application.controlled_values import (
    CatalogValueDocument,
    LocalConcept,
)
from libris.modules.bibliographic.application.vocabulary_resolution import (
    EnrichedConcept,
    ResolutionCachePolicy,
)
from libris.modules.bibliographic.domain.vocabularies import VocabularyRegistry
from libris.modules.bibliographic.infrastructure.serialization.controlled_values import (
    catalog_value_to_graph,
    local_concept_to_graph,
)
from libris.modules.bibliographic.infrastructure.serialization.representation import serialize_graph

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "docs/examples/controlled-vocabularies"
SCHEMA = ROOT / "apps/api/src/libris/modules/bibliographic/resources/controlled-values-v1"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    artifacts = {
        SCHEMA / "catalog-value-1.0.schema.json": json.dumps(
            CatalogValueDocument.model_json_schema(), ensure_ascii=False, indent=2
        )
        + "\n"
    }
    for name, model in (
        ("enriched-concept", EnrichedConcept),
        ("cache-policy", ResolutionCachePolicy),
        ("vocabulary-registry", VocabularyRegistry),
    ):
        artifacts[SCHEMA / f"{name}-1.0.schema.json"] = (
            json.dumps(model.model_json_schema(), ensure_ascii=False, indent=2) + "\n"
        )
    for name in ("external", "local"):
        document = CatalogValueDocument.model_validate_json((EXAMPLES / f"{name}.json").read_text())
        graph = (
            local_concept_to_graph(document.value)
            if isinstance(document.value, LocalConcept)
            else catalog_value_to_graph(
                "https://example.org/resources/00000000-0000-4000-8000-000000000001",
                "http://id.loc.gov/ontologies/bibframe/language",
                document.value,
            )
        )
        for format, suffix in (("json-ld", "jsonld"), ("turtle", "ttl")):
            # Turtle blank node/prefix order is not an artifact invariant: checked as RDF below.
            artifacts[EXAMPLES / f"{name}.{suffix}"] = serialize_graph(graph, format=format)
    from rdflib.compare import isomorphic

    from libris.modules.bibliographic.infrastructure.serialization import parse_representation

    for path, content in artifacts.items():
        if args.check:
            if not path.exists():
                raise SystemExit(f"Artefato ausente: {path}")
            matches = (
                isomorphic(
                    parse_representation(
                        path.read_text(), "turtle" if path.suffix == ".ttl" else "json-ld"
                    ),
                    parse_representation(content, "turtle" if path.suffix == ".ttl" else "json-ld"),
                )
                if path.suffix in {".ttl", ".jsonld"}
                else path.read_text() == content
            )
            if not matches:
                raise SystemExit(f"Artefato divergente: {path}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    print(f"{len(artifacts)} artefatos {'verificados' if args.check else 'gerados'}.")


if __name__ == "__main__":
    main()
