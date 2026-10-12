"""Regenera exemplos sintéticos a partir das fixtures Read da issue #18."""

import json
from pathlib import Path

from rdflib import URIRef

from libris.modules.bibliographic.api.schemas import (
    AgentRead,
    InstanceRead,
    ItemRead,
    SubjectRead,
    WorkRead,
)
from libris.modules.bibliographic.infrastructure.serialization import (
    ResourceRead,
    resource_to_graph,
    serialize_composed,
    serialize_resource,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/bibliographic/serialization/valid"
OUTPUT = ROOT / "docs/examples/serialization"


def main() -> None:
    resources: list[ResourceRead] = []
    for name, schema in [
        ("work", WorkRead),
        ("instance", InstanceRead),
        ("item", ItemRead),
        ("agent", AgentRead),
        ("subject", SubjectRead),
        ("organization", AgentRead),
    ]:
        resource = schema.model_validate_json((FIXTURES / f"{name}.json").read_text())
        resources.append(resource)
        (OUTPUT / f"{name}.json").write_text(
            json.dumps(resource.model_dump(mode="json"), ensure_ascii=False, indent=2)
            + "\n",
            encoding="utf-8",
        )
        for format, extension in [("json-ld", "jsonld"), ("turtle", "ttl")]:
            (OUTPUT / f"{name}.{extension}").write_text(
                serialize_resource(resource, format=format), encoding="utf-8"
            )
    (OUTPUT / "related.json").write_text(
        json.dumps(
            [resource.model_dump(mode="json") for resource in resources],
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    snapshots = [
        (URIRef(resource.uri), resource_to_graph(resource)) for resource in resources
    ]
    for format, extension in [("json-ld", "jsonld"), ("turtle", "ttl")]:
        (OUTPUT / f"related.{extension}").write_text(
            serialize_composed(snapshots, format=format), encoding="utf-8"
        )


if __name__ == "__main__":
    main()
