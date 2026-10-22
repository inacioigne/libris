# Backend Agent Instructions — Libris

## Scope

These instructions apply to the `backend/` directory.

Follow the root `AGENTS.md` and the project architecture documentation.

## Technology

- Python 3.12+
- FastAPI
- Pydantic v2
- RDFLib
- pySHACL
- pytest

## Architecture

- Organize code around cohesive domain modules.
- Keep API routes thin.
- Separate validation, domain logic, serialization, and persistence responsibilities.
- Reuse existing models and contracts.
- Avoid unnecessary dependencies.
- Do not assume that proposed infrastructure is already deployed.

## Bibliographic contracts

- Preserve the distinction between BIBFRAME Work, Instance, and Item.
- Maintain unique persistent resource identifiers.
- Reject unsupported RDF properties when a lossless transformation cannot be guaranteed.
- Respect existing SHACL shapes.
- Preserve JSON and JSON-LD contract compatibility.
- Do not silently change the cardinality of metadata fields.

## Testing

Work from `backend/`.

Run applicable tests:

```bash
python -m pytest tests/api
python -m pytest tests/contracts
```

Before using these commands, verify that dependencies and referenced modules are available.

When changing bibliographic models or RDF serialization, add regression tests covering validation, graph transformations, and round-trip behavior.

## API development

- Follow `docs/api/openapi.yaml`.
- Maintain consistent validation and error handling.
- Document API contract changes.
- Do not claim that a proposed endpoint is implemented without checking the source code.

## Completion

Describe modified files, validations performed, test results, compatibility implications, and remaining work.