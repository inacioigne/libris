"""Agent contracts for the candidate local profile."""

from typing import Literal

from pydantic import Field

from .common import (
    Contract,
    Identifier,
    LocalizedText,
    PartialContract,
    ReadIdentity,
    ResourceReference,
    UniqueTexts,
    non_nullable_schema,
)

AgentKind = Literal["Agent", "Person", "Organization"]


class AgentCreate(Contract):
    kind: AgentKind
    authorized_name: UniqueTexts
    variant_name: list[LocalizedText] = Field(default_factory=list)
    identified_by: list[Identifier] = Field(default_factory=list)
    external_reference: list[ResourceReference] = Field(default_factory=list)
    provenance: list[ResourceReference] = Field(default_factory=list)
    related_authority: list[ResourceReference] = Field(default_factory=list)


class AgentRead(AgentCreate, ReadIdentity):
    """Owned description and stored identity; no technical audit columns."""


class AgentUpdate(PartialContract):
    required_fields = frozenset(["authorized_name"])

    authorized_name: UniqueTexts | None = Field(default=None, json_schema_extra=non_nullable_schema)
    variant_name: list[LocalizedText] | None = None
    identified_by: list[Identifier] | None = None
    external_reference: list[ResourceReference] | None = None
    provenance: list[ResourceReference] | None = None
    related_authority: list[ResourceReference] | None = None
