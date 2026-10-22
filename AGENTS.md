# AGENTS.md — Libris

## 1. Project identity

Libris is an open-source, enterprise-grade Integrated Library System (ILS) built around Semantic Web principles and Linked Open Data.

The project uses BIBFRAME as its primary bibliographic model, while supporting additional ontologies and vocabularies.

Its goal is to combine traditional library management with entity-oriented cataloging, linked-data interoperability, and modern discovery experiences.

## 2. Technology stack

Target architecture:

- Backend: Python 3.12+, FastAPI, Pydantic.
- Frontend: Next.js, React, TypeScript.
- Search and discovery: Elasticsearch.
- Bibliographic metadata: BIBFRAME, RDF, JSON-LD, SHACL.
- Data storage: follow approved architectural decisions.

Do not assume that planned components have already been implemented.

## 3. Mandatory documentation

Before making changes, read the relevant documents:

- `docs/architecture/overview.md`
- `docs/architecture/principles.md`
- `docs/domain/bibliographic.md`
- `docs/api/openapi.yaml`
- `docs/architecture/decisions/`

When working in a directory containing a more specific `AGENTS.md`, follow its applicable instructions as well.

If a document is missing or empty, inspect the code and existing contracts rather than inventing project decisions.

## 4. Architectural principles

- Favor modular design with explicit domain boundaries.
- Separate bibliographic metadata from operational library management.
- Treat BIBFRAME entities and relationships as first-class domain concepts.
- Use persistent identifiers for bibliographic resources.
- Support controlled vocabularies and semantic interoperability.
- Preserve existing data contracts unless a change is explicitly required.
- Favor incremental, testable implementations.
- Avoid premature abstractions and unnecessary dependencies.

## 5. Development rules

- Examine existing implementations before creating new abstractions.
- Maintain compatibility with existing APIs and data representations.
- Use type annotations and validated domain models.
- Keep business logic separate from HTTP transport concerns.
- Do not modify unrelated functionality.
- Add or update tests for meaningful behavioral changes.
- Update documentation when changing architecture, contracts, or domain behavior.
- Never introduce credentials or secrets into source code.

## 6. Bibliographic and semantic rules

- BIBFRAME is the primary bibliographic model.
- Maintain the distinction between Work, Instance, and Item.
- Preserve entity relationships and identifier semantics.
- Avoid lossy RDF or JSON-LD transformations.
- Respect published SHACL validation profiles.
- Do not silently discard unsupported semantic properties.
- Treat authority records as reusable entities.

## 7. Agent workflow

For each implementation task:

1. Understand the request and inspect relevant source code.
2. Identify applicable documentation and contracts.
3. Determine whether an architectural decision is required.
4. Implement the smallest coherent change.
5. Add or update relevant automated tests.
6. Run appropriate validation commands.
7. Review the diff for unrelated changes.
8. Summarize the implementation and remaining limitations.

Never claim that tests passed unless they were actually executed.

## 8. Git and pull requests

- Use focused branches and commits.
- Do not commit directly to `main` unless explicitly authorized.
- Do not perform destructive Git operations without explicit authorization.
- Do not close issues merely because code was written.
- Explain how each completed task satisfies its acceptance criteria.

## 9. Completion criteria

A task is complete when:

- The requested behavior is implemented.
- Relevant tests pass, or test limitations are reported.
- Contracts and semantic invariants are preserved.
- Documentation is updated when necessary.
- The scope and limitations of the change are clearly communicated.