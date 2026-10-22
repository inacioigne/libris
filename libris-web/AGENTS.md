<!-- BEGIN:nextjs-agent-rules -->

## This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->

# AGENTS.md — Libris Web

## Purpose and scope

These rules apply to all files under `libris-web/` and complement the repository root `AGENTS.md`. Follow applicable root instructions and approved architectural decisions; this file specifies frontend responsibilities. Do not treat proposed features as already implemented.

Libris is an open-source, modular, enterprise-grade integrated library system (ILS) combining library operations with Semantic Web and Linked Open Data. BIBFRAME is the primary bibliographic model, with extensibility for other ontologies and controlled vocabularies.

The frontend is **one Next.js application with two clearly separated product areas**:

1. **Public OPAC (Online Public Access Catalog)** — accessible discovery of physical and digital collections, authors, subjects, institutions, and their semantic relationships.
2. **Administration (staff interface)** — authenticated workspace for librarians and authorized staff to catalog, manage authorities, circulation, acquisitions, serials, patrons, and reporting.

Different audiences, workflows, visual densities, navigation, authorization requirements, and loading strategies are intentional. Share design primitives and typed integrations, not unrelated page states or domain rules.

## Actual stack and current status

- Application: `libris-web/` using **Next.js 16.4.2**, **React 19.3**, **TypeScript 5**, **Tailwind CSS 4**, and **ESLint 9**.
- Next.js App Router: `app/` currently contains the starter layout, page, and global stylesheet.
- Package manager: npm (`package-lock.json` is tracked).
- API: `libris-api/` (FastAPI); discovery/search is intended to use Elasticsearch **behind the API**.
- Planned modules and routes below are targets, not claims of existing features.
- Before changing code, inspect `package.json`, the relevant existing source, root `AGENTS.md`, `docs/api/openapi.yaml`, `docs/domain/`, `docs/architecture/`, and ADRs when present.
- Inspect the **installed Next.js documentation at `node_modules/next/dist/docs/`** before implementing Next.js-specific APIs or conventions; do not rely on older framework assumptions.

## Boundaries and suggested organization

Prefer a single App Router deployment with route groups and separate layouts. Route groups do not change URLs. Keep existing routes intact unless changing them is part of the task.

```text
libris-web/
  app/
    (opac)/              # Public-facing route group
      layout.tsx
      page.tsx
      search/
      works/
      instances/
      authors/
      subjects/
    (admin)/             # Staff route group
      admin/
        layout.tsx
        page.tsx
        cataloging/
        authorities/
        circulation/
        acquisitions/
        serials/
        patrons/
        reports/
  components/
    ui/                  # Shared accessible, presentational components
    opac/                # Public discovery components
    admin/               # Staff workflow components
  features/              # Feature-specific UI, hooks, schemas and adapters
  lib/
    api/                 # Centralized typed API clients and DTO mappings
    auth/                # Authentication/session helpers
    bibliographic/       # Domain types and read-only representation utilities
```

This layout is **guidance**, not authorization to create every folder or reorganize code speculatively. Avoid putting route-specific components in global shared folders. Do not expose server-only modules to client bundles.

## Public OPAC requirements

- Prioritize fast, intuitive, accessible discovery over administrative complexity.
- Implement a prominent simple search and an advanced search only where needed.
- Plan for relevance sorting, facets with clear active states, pagination, empty/error/loading states, and URL-shareable query/filter parameters.
- Represent **BIBFRAME Work, Instance, and Item** distinctly: a Work can group editions/publications (Instances), each with its own holdings (Items) and availability where exposed by the API.
- Enable navigation among works, editions, creators, organizations, subjects, and related entities via stable identifiers. Never infer graph relationships solely from matching display labels.
- Use readable catalog records with covers when available, language, publication details, format, identifiers, location, and authoritative availability. Provide accessible fallbacks when images or metadata are missing.
- Only display availability, borrowing options, reservations, and account data when supported by live API contracts; do not simulate operational status.
- Make public catalog pages indexable where appropriate, with meaningful titles/metadata, canonical URLs, and sensible server rendering.
- Never leak unpublished records, private patron details, internal notes, or administration-only endpoints in public payloads.

### OPAC UX references

Use **VuFind** and **Primo NDE** for search and discovery UX, and **Share-VDE** for entity-based navigation. Borrow concepts, not assets, layouts, or code without appropriate authorization.

## Administration requirements

- Treat the staff interface as a task-oriented workspace: efficient navigation, clear information hierarchy, predictable forms, bulk actions where supported, and visible feedback.
- Major business areas include cataloging, authority control, circulation, acquisitions, serials, patrons, and reports/statistics. Implement incrementally and according to validated backend contracts.
- **Cataloging is entity-oriented and BIBFRAME-first**. Offer librarian-friendly forms and repeatable fields/properties based on approved metadata profiles; do not require users to edit raw RDF for everyday tasks.
- Preserve distinctions among Work, Instance, Item, people/organizations, subjects, and their relations. Do not flatten them into one generic bibliographic record.
- Support controlled values, persistent IDs, authority lookup/linking, validation feedback, and safe handling of multilingual metadata when contracts permit.
- Model draft, create, edit, review, publish, cancel and error states explicitly when relevant; never assume all are supported by the API.
- Require explicit confirmation before destructive operations. Avoid silent loss of unsaved edits; show field-level errors and meaningful mutation outcomes.
- Display audit/provenance/history only when supplied by backend capabilities; do not invent attribution.
- Keep access checks both in the server/backend and appropriate frontend guards. Hiding menu items **is not authorization**.
- Keep administrative screens usable on common desktop widths and accessible on smaller screens; prioritize dense-but-readable tables, keyboard workflows, filters, and clear status labels.

### Admin UX references

Use **FOLIO** for modular workflows, **Koha** for essential library operations, and **MARVA/Sinopia** for BIBFRAME-oriented forms. Do not clone their implementation or assume their internal business rules match Libris.

## API integration and security

- FastAPI is the authoritative source for domain rules, permissions, transactions, catalog records and search results.
- Treat `docs/api/openapi.yaml` and actual backend endpoints as contracts, while checking for mismatches; never fabricate endpoints, payload fields, permissions, or search response shapes.
- Centralize API calls and typed DTO-to-view-model transformations. Validate untrusted responses at boundaries when appropriate; provide distinguishable loading, empty, error and permission-denied states.
- Do not query Elasticsearch, PostgreSQL, or an RDF store directly from browser code. All access goes through approved backend interfaces.
- Avoid embedding credentials, access tokens, secrets, internal service addresses, or patron information in client code, logs, static generation, or public metadata.
- Prefer secure server-side session/cookie handling and backend authorization; do not use localStorage as the source of truth for privileged identity.
- Prevent cross-user data leakage through caching: distinguish public cacheable catalog responses from authenticated/no-store staff or patron responses.
- Handle session expiry and 401/403 responses distinctly and without redirect loops.
- Use JSON-LD/RDF semantics carefully: preserve stable URIs, relationship identifiers, language tags and repeatable values; no lossy transformation or silent dropping of unsupported properties.

## Next.js and React development

- Prefer React Server Components for data retrieval/rendering and Client Components only for necessary interactivity.
- Mark `"use client"` only at the smallest meaningful interactive boundary; avoid shipping server-only dependencies to the browser.
- Use App Router route segments, layouts, loading/error/not-found boundaries, and route groups according to **the installed Next.js 16 docs**.
- Use TypeScript strictness, explicit domain types and discriminated unions for complex UI states. Avoid `any`, arbitrary casts, and duplicating API types manually without a source contract.
- Keep URL state for discoverable OPAC queries; keep local interaction state near the consuming feature. Avoid introducing a global state library prematurely.
- Keep components cohesive and reusable where reuse is real, with semantic naming. Favor composition over a universal component with many unrelated flags.
- Use Tailwind CSS 4 and existing styles consistently. Introduce component libraries only after checking dependency, accessibility and maintenance implications.
- Optimize images, fonts and bundle size; do not introduce large libraries to solve trivial UI problems.
- Provide meaningful metadata, avoid layout shift, and design for slow networks.

## Accessibility and internationalization

- Target **WCAG 2.2 AA** in new UI: semantic HTML, labels, logical focus order, keyboard access, visible focus states, sufficient contrast, accessible dialogs, and descriptive error messages.
- Do not rely on color alone for status. Ensure forms announce errors and dynamic results have appropriate accessible feedback.
- Use Brazilian Portuguese as the initial interface language unless product requirements specify otherwise. Keep translatable UI strings centralized instead of embedding scattered strings.
- Preserve the **original language and script** of bibliographic titles, names and descriptions. Interface translation must never rewrite source metadata.
- Use locale-aware formatting for dates/numbers, and respect metadata language tags and diacritics.

## Quality, tests and delivery

Before implementation, identify the affected area (OPAC, admin, or shared), inspect existing patterns, and confirm relevant API contracts. Implement the smallest coherent change.

Test as appropriate:
- Search controls, URL/query and facet synchronization, empty/error states, and entity links for OPAC.
- Form validation, authority selection, unsaved changes, permissions and destructive confirmations for admin.
- Server/client boundaries, authentication response handling, and cache isolation.
- Keyboard navigation and accessible names for critical interactive components.

From `libris-web/`, run when dependencies are installed:

```bash
npm ci
npm run lint
npx tsc --noEmit
npm run build
```

No test runner is currently declared in `package.json`; do not claim `npm test` exists. Propose a suitable setup before writing tests that rely on new tooling. Report checks actually run and failures encountered.

## Agent conduct and completion

1. Read the root and local `AGENTS.md`, relevant code, API schemas, and up-to-date installed framework docs.
2. State which area the task affects and preserve its UX and security boundaries.
3. Avoid unrelated refactors, arbitrary dependencies, and speculative backend changes.
4. Preserve BIBFRAME distinctions, controlled vocabularies, identifiers, and metadata fidelity.
5. Implement accessible loading, error and empty states rather than happy-path-only UI.
6. Update tests/documentation for meaningful behavior or architectural changes.
7. Review the diff; never overwrite generated agent rules or unrelated user work.
8. Summarize files changed, tests actually executed, outstanding backend dependencies, and limitations.

Do not commit directly to `main` unless explicitly authorized. Do not close issues until acceptance criteria are verified. When backend capability is not yet implemented, distinguish a documented UI proposal from a working integration.
