"""Authorized keyset listing with scope-bound continuation, without totals/history."""

import base64
import binascii
import hashlib
import json
from uuid import UUID

from libris.modules.bibliographic.api.schemas.listing import (
    CatalogPage,
    EditorialCatalogQuery,
    PublicCatalogQuery,
)
from libris.modules.bibliographic.application.catalog import CatalogService
from libris.modules.bibliographic.domain.editorial import EditorialState
from libris.modules.bibliographic.domain.errors import CatalogCode, CatalogError
from libris.modules.bibliographic.domain.relationships import EntityType
from libris.modules.bibliographic.infrastructure.catalog_query import (
    catalog_rows,
    catalog_statement,
)
from libris.modules.bibliographic.infrastructure.rdf import parse_document
from libris.modules.bibliographic.infrastructure.serialization import ResourceRead, graph_to_read
from libris.modules.identity.application.authorization import HumanContext
from libris.modules.identity.domain.authorization import Operation, ResourceContext, ResourceKind


def scope_digest(entity: EntityType, public: bool, query: PublicCatalogQuery) -> str:
    material = [
        "catalog-page-v1",
        entity.value,
        public,
        "internal_id:asc",
        query.model_dump(mode="json", exclude={"cursor"}),
    ]
    return hashlib.sha256(json.dumps(material, sort_keys=True).encode()).hexdigest()


def encode_cursor(after: UUID, scope: str) -> str:
    return base64.urlsafe_b64encode(f"1:{after}:{scope}".encode()).decode().rstrip("=")


def decode_cursor(cursor: str | None, scope: str) -> UUID | None:
    if cursor is None:
        return None
    try:
        raw = base64.b64decode(cursor + "=" * (-len(cursor) % 4), altchars=b"-_", validate=True)
        version, identifier, stored_scope = raw.decode("ascii").split(":")
        after = UUID(identifier)
        if version != "1" or stored_scope != scope or encode_cursor(after, scope) != cursor:
            raise ValueError("Cursor incompatível")
        return after
    except (ValueError, UnicodeError, binascii.Error) as error:
        raise CatalogError(
            CatalogCode.MALFORMED_REQUEST, "Cursor inválido ou incompatível."
        ) from error


async def list_catalog(
    service: CatalogService,
    entity: EntityType,
    query: PublicCatalogQuery,
    *,
    public: bool,
    context: HumanContext | None = None,
) -> CatalogPage[ResourceRead]:
    authority = entity in {EntityType.AGENT, EntityType.SUBJECT}
    kind = ResourceKind.AUTHORITY if authority else ResourceKind.BIBLIOGRAPHIC
    operation = (
        (Operation.AUTHORITY_READ_PUBLIC if authority else Operation.BIBLIOGRAPHIC_READ_PUBLIC)
        if public
        else (
            Operation.AUTHORITY_READ_EDITORIAL
            if authority
            else Operation.BIBLIOGRAPHIC_READ_EDITORIAL
        )
    )
    if not public:
        service.authorization.require(
            context=context,
            operation=operation,
            resource=ResourceContext(kind),
        )
    scope = scope_digest(entity, public, query)
    after = decode_cursor(query.cursor, scope)
    statement = catalog_statement(
        entity,
        public=public,
        limit=query.limit + 1,
        after=after,
        internal_id=query.internal_id,
        uri=query.uri,
        profile=query.profile,
        editorial_state=query.editorial_state if isinstance(query, EditorialCatalogQuery) else None,
    )
    async with service.sessions() as session:
        rows = await catalog_rows(session, statement)
    page = rows[: query.limit]
    if public:
        for identity, number, _ in page:
            service.authorization.require(
                context=None,
                operation=operation,
                resource=ResourceContext(
                    kind,
                    EditorialState.PUBLISHED,
                    number,
                    number,
                    resource_id=identity.internal_id,
                ),
            )
    return CatalogPage(
        items=[
            graph_to_read(parse_document(json.dumps(document), "json-ld"), identity)
            for identity, _, document in page
        ],
        next_cursor=encode_cursor(page[-1][0].internal_id, scope)
        if len(rows) > query.limit
        else None,
        limit=query.limit,
    )
