"""Operational catalog values v1; reusable by cataloging and authorities, without I/O."""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, model_validator

from libris.modules.bibliographic.api.schemas.common import (
    IRI,
    Contract,
    EntityReference,
    LanguageTag,
    LocalizedText,
    ResourceReference,
    ResourceURI,
    Text,
    disjoint_labels,
    unique_languages,
)
from libris.modules.bibliographic.domain.profile_contract import DATATYPES, XSD, valid_lexical

ReferenceStatus = Literal["resolved", "unverified", "invalid", "deprecated", "unavailable"]


class LiteralValue(Contract):
    """RDF lexical value: numeric/date lexicals remain strings, without coercion."""

    kind: Literal["literal"]
    value: Annotated[str, Field(strict=True)]
    language: LanguageTag | None = None
    datatype: IRI | None = None

    @model_validator(mode="after")
    def consistent(self) -> "LiteralValue":
        if self.language is not None and self.datatype is not None:
            raise ValueError("Idioma e datatype explícito são mutuamente exclusivos.")
        if self.datatype is not None and (
            self.datatype not in DATATYPES or not valid_lexical(self.value, self.datatype)
        ):
            raise ValueError("Datatype ou forma lexical não suportados nesta release.")
        return self


class ConceptValue(Contract):
    uri: IRI
    vocabulary: IRI
    label: list[LocalizedText] = Field(default_factory=list)
    alternative_labels: list[LocalizedText] = Field(default_factory=list)
    notation: Text | None = None
    source: IRI | None = None
    status: ReferenceStatus = "unverified"
    replacement: IRI | None = None

    @model_validator(mode="after")
    def consistent(self) -> "ConceptValue":
        unique_languages(self.label)
        disjoint_labels(self.label, self.alternative_labels)
        for texts in (self.label, self.alternative_labels):
            terms = [(text.value, (text.language or "").lower()) for text in texts]
            if len(set(terms)) != len(terms) or any(not text.value.strip() for text in texts):
                raise ValueError("Rótulos vazios ou duplicados.")
        if self.status in {"resolved", "invalid", "deprecated"} and self.source is None:
            raise ValueError("Estado confirmado exige fonte; sintaxe não confirma existência.")
        if self.replacement is not None and (
            self.status != "deprecated" or self.replacement == self.uri
        ):
            raise ValueError("Sucessor distinto exige conceito deprecated.")
        return self

    def as_reference(self) -> ResourceReference:
        """Explicit compatibility projection; presentation metadata stays in this value."""
        return ResourceReference(uri=self.uri)


class ControlledConcept(ConceptValue):
    kind: Literal["controlled_concept"]


class LocalConcept(ConceptValue):
    kind: Literal["local_concept"]
    internal_id: UUID
    uri: ResourceURI


class EntityValue(Contract):
    kind: Literal["entity_reference"]
    reference: EntityReference


CatalogValue = Annotated[
    LiteralValue | ControlledConcept | LocalConcept | EntityValue, Field(discriminator="kind")
]


class CatalogValueDocument(Contract):
    """Versioned operational envelope, not a bibliographic snapshot."""

    format: Literal["libris.catalog-value"] = "libris.catalog-value"
    contract_version: Literal["1.0"] = "1.0"
    value: CatalogValue


STRING_DATATYPE = XSD + "string"


def parse_catalog_value(payload: object) -> CatalogValue:
    return CatalogValueDocument.model_validate({"value": payload}).value
