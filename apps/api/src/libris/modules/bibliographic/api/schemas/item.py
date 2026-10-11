"""Item contracts for the candidate local profile."""

from pydantic import Field

from .common import (
    Contract,
    ItemIdentifiers,
    LocalizedText,
    Note,
    PartialContract,
    ReadIdentity,
    ResourceReference,
    ShelfMark,
    non_nullable_schema,
)


class ItemCreate(Contract):
    item_of: ResourceReference
    identified_by: ItemIdentifiers
    held_by: list[ResourceReference] = Field(default_factory=list)
    note: list[Note] = Field(default_factory=list)
    custodial_history: list[LocalizedText] = Field(default_factory=list)
    shelf_mark: list[ShelfMark] = Field(default_factory=list)
    provenance: list[ResourceReference] = Field(default_factory=list)


class ItemRead(ItemCreate, ReadIdentity):
    """Owned description and stored identity; no technical audit columns."""


class ItemUpdate(PartialContract):
    required_fields = frozenset(["item_of", "identified_by"])

    item_of: ResourceReference | None = Field(default=None, json_schema_extra=non_nullable_schema)
    identified_by: ItemIdentifiers | None = Field(
        default=None, json_schema_extra=non_nullable_schema
    )
    held_by: list[ResourceReference] | None = None
    note: list[Note] | None = None
    custodial_history: list[LocalizedText] | None = None
    shelf_mark: list[ShelfMark] | None = None
    provenance: list[ResourceReference] | None = None
