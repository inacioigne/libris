"""Closed query parameters and typed, bounded catalog pages."""

from typing import Literal
from uuid import UUID

from pydantic import Field

from libris.modules.bibliographic.api.schemas.common import Contract, ResourceURI
from libris.modules.bibliographic.domain.editorial import EditorialState
from libris.modules.bibliographic.infrastructure.serialization import ResourceRead


class PublicCatalogQuery(Contract):
    limit: int = Field(default=20, ge=1, le=100)
    cursor: str | None = Field(default=None, min_length=1, max_length=4096)
    internal_id: UUID | None = None
    uri: ResourceURI | None = None
    profile: str | None = Field(default=None, min_length=1, max_length=200)


class EditorialCatalogQuery(PublicCatalogQuery):
    editorial_state: EditorialState | None = None


class CatalogPage[T: ResourceRead](Contract):
    items: list[T]
    next_cursor: str | None
    limit: int
    order: Literal["internal_id:asc"] = "internal_id:asc"
