"""Work contracts for the candidate local profile."""

from pydantic import Field

from .common import (
    Classification,
    Contract,
    Contribution,
    Note,
    PartialContract,
    ReadIdentity,
    ResourceReference,
    SubjectReference,
    WorkReference,
    WorkTitles,
    non_nullable_schema,
)


class WorkCreate(Contract):
    title: WorkTitles
    language: list[ResourceReference] = Field(default_factory=list)
    content: list[ResourceReference] = Field(default_factory=list)
    contribution: list[Contribution] = Field(default_factory=list)
    subject: list[SubjectReference] = Field(default_factory=list)
    classification: list[Classification] = Field(default_factory=list)
    related_to: list[WorkReference] = Field(default_factory=list)
    translation_of: list[WorkReference] = Field(default_factory=list)
    note: list[Note] = Field(default_factory=list)


class WorkRead(WorkCreate, ReadIdentity):
    """Owned description and stored identity; no technical audit columns."""


class WorkUpdate(PartialContract):
    required_fields = frozenset(["title"])

    title: WorkTitles | None = Field(default=None, json_schema_extra=non_nullable_schema)
    language: list[ResourceReference] | None = None
    content: list[ResourceReference] | None = None
    contribution: list[Contribution] | None = None
    subject: list[SubjectReference] | None = None
    classification: list[Classification] | None = None
    related_to: list[WorkReference] | None = None
    translation_of: list[WorkReference] | None = None
    note: list[Note] | None = None
