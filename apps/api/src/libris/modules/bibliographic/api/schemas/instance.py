"""Instance contracts for the candidate local profile."""

from pydantic import Field

from .common import (
    Contract,
    Extent,
    Identifier,
    LocalizedText,
    Note,
    PartialContract,
    Publication,
    ReadIdentity,
    ResourceReference,
    Title,
    non_nullable_schema,
)


class InstanceCreate(Contract):
    instance_of: ResourceReference
    title: list[Title] = Field(default_factory=list)
    edition_statement: list[LocalizedText] = Field(default_factory=list)
    provision_activity: list[Publication] = Field(default_factory=list)
    identified_by: list[Identifier] = Field(default_factory=list)
    extent: list[Extent] = Field(default_factory=list)
    carrier: list[ResourceReference] = Field(default_factory=list)
    note: list[Note] = Field(default_factory=list)


class InstanceRead(InstanceCreate, ReadIdentity):
    """Owned description and stored identity; no technical audit columns."""


class InstanceUpdate(PartialContract):
    required_fields = frozenset(["instance_of"])

    instance_of: ResourceReference | None = Field(
        default=None, json_schema_extra=non_nullable_schema
    )
    title: list[Title] | None = None
    edition_statement: list[LocalizedText] | None = None
    provision_activity: list[Publication] | None = None
    identified_by: list[Identifier] | None = None
    extent: list[Extent] | None = None
    carrier: list[ResourceReference] | None = None
    note: list[Note] | None = None
