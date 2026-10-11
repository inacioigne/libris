"""Subject contracts for the candidate local profile."""

from pydantic import Field, model_validator

from .common import (
    Contract,
    LocalizedText,
    PartialContract,
    ReadIdentity,
    RequiredReferences,
    ResourceReference,
    UniqueTexts,
    disjoint_labels,
    non_nullable_schema,
)


class SubjectCreate(Contract):
    preferred_label: UniqueTexts
    alternative_label: list[LocalizedText] = Field(default_factory=list)
    scheme: RequiredReferences
    broader: list[ResourceReference] = Field(default_factory=list)
    related: list[ResourceReference] = Field(default_factory=list)
    external_reference: list[ResourceReference] = Field(default_factory=list)
    provenance: list[ResourceReference] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_labels(self) -> "SubjectCreate":
        disjoint_labels(self.preferred_label, self.alternative_label)
        return self


class SubjectRead(SubjectCreate, ReadIdentity):
    """Owned description and stored identity; no technical audit columns."""


class SubjectUpdate(PartialContract):
    required_fields = frozenset(["preferred_label", "scheme"])

    preferred_label: UniqueTexts | None = Field(default=None, json_schema_extra=non_nullable_schema)
    alternative_label: list[LocalizedText] | None = None
    scheme: RequiredReferences | None = Field(default=None, json_schema_extra=non_nullable_schema)
    broader: list[ResourceReference] | None = None
    related: list[ResourceReference] | None = None
    external_reference: list[ResourceReference] | None = None
    provenance: list[ResourceReference] | None = None

    @model_validator(mode="after")
    def check_supplied_labels(self) -> "SubjectUpdate":
        if self.preferred_label is not None and self.alternative_label is not None:
            disjoint_labels(self.preferred_label, self.alternative_label)
        return self
