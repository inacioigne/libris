"""Entradas HTTP limitadas; configurações e shapes vêm somente do registro local."""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field

from libris.modules.bibliographic.api.schemas import (
    AgentCreate,
    InstanceCreate,
    ItemCreate,
    SubjectCreate,
    WorkCreate,
)
from libris.modules.bibliographic.api.schemas.common import IRI, Contract

ResourceCreate = WorkCreate | InstanceCreate | ItemCreate | AgentCreate | SubjectCreate


class DtoValidation(Contract):
    kind: Literal["dto"]
    profile_release: IRI
    resource: ResourceCreate


class RdfValidation(Contract):
    kind: Literal["rdf"]
    profile_release: IRI
    format: Literal["json-ld", "turtle"]
    document: str
    root: IRI
    context: Literal["snapshot", "composed"] = "snapshot"


class RevisionValidation(Contract):
    kind: Literal["revision"]
    resource_id: UUID
    revision: int | None = Field(default=None, ge=1)


ValidationRequest = Annotated[
    DtoValidation | RdfValidation | RevisionValidation, Field(discriminator="kind")
]
