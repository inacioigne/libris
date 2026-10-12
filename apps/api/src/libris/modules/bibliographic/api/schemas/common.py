"""Structural JSON types for the local catalogographic profiles."""

import re
from typing import Annotated, ClassVar, Literal
from urllib.parse import urlsplit
from uuid import UUID

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator
from pydantic.config import JsonDict

from libris.modules.bibliographic.domain.models import ResourceIdentity
from libris.modules.bibliographic.domain.profiles import absolute_iri
from libris.modules.bibliographic.domain.relationships import EntityType


def validate_iri(value: str) -> str:
    absolute_iri(value)
    if re.search(r'[\x00-\x20<>"{}|\\^`\x7f]', value):
        raise ValueError("A IRI contém caracteres inválidos.")
    if re.search(r"%(?![0-9a-fA-F]{2})", value):
        raise ValueError("Escape percentual inválido na IRI.")
    parts = urlsplit(value)
    if parts.scheme in {"http", "https"}:
        if not parts.hostname:
            raise ValueError("A IRI HTTP(S) exige um host.")
        # Accessing port checks its numeric form and range without rewriting the IRI.
        _ = parts.port
    if not value.partition(":")[2]:
        raise ValueError("A IRI exige uma parte específica do esquema.")
    return value


def validate_resource_uri(value: str) -> str:
    ResourceIdentity(UUID(int=0), value)
    return value


IRI = Annotated[str, Field(min_length=1, strict=True), AfterValidator(validate_iri)]
ResourceURI = Annotated[IRI, AfterValidator(validate_resource_uri)]
Text = Annotated[str, Field(min_length=1, strict=True)]
# RDFLib's language-tag syntax: structural validation, without registry lookup.
LanguageTag = Annotated[str, Field(pattern=r"^[a-zA-Z]+(?:-[a-zA-Z0-9]+)*$", strict=True)]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PartialContract(Contract):
    """Absent means unchanged; null clears only optional bibliographic properties."""

    required_fields: ClassVar[frozenset[str]] = frozenset()

    @model_validator(mode="before")
    @classmethod
    def reject_required_null(cls, value: object) -> object:
        if isinstance(value, dict):
            for name in cls.required_fields:
                if name in value and value[name] is None:
                    raise ValueError(f"{name} não admite null.")
        return value


def non_nullable_schema(schema: JsonDict) -> None:
    """Omission is allowed in PATCH, but explicit null is not."""
    alternatives = schema.pop("anyOf", None)
    if isinstance(alternatives, list):
        for alternative in alternatives:
            if isinstance(alternative, dict) and alternative.get("type") != "null":
                schema.update(alternative)
    schema.pop("default", None)


class ReadIdentity(Contract):
    internal_id: UUID
    uri: ResourceURI


class ResourceReference(Contract):
    """URI-only reference: target class comes from the owning property/profile."""

    uri: IRI


class LocalReference(Contract):
    kind: Literal["local"] = "local"
    entity_type: EntityType
    internal_id: UUID | None = None
    uri: ResourceURI | None = None

    @model_validator(mode="after")
    def require_identity(self) -> "LocalReference":
        if self.internal_id is None and self.uri is None:
            raise ValueError("Referência local exige UUID e/ou URI armazenada.")
        return self


class ExternalReference(Contract):
    kind: Literal["external"] = "external"
    entity_type: EntityType
    uri: IRI
    namespace: IRI | None = None
    external_id: Text | None = None

    @model_validator(mode="after")
    def require_namespace(self) -> "ExternalReference":
        if self.external_id is not None and self.namespace is None:
            raise ValueError("Identificador externo exige namespace.")
        return self


class UnreconciledReference(Contract):
    kind: Literal["unreconciled"] = "unreconciled"
    entity_type: EntityType
    label: Text
    namespace: IRI
    key: Text

    @model_validator(mode="after")
    def non_blank(self) -> "UnreconciledReference":
        if not self.label.strip() or not self.key.strip():
            raise ValueError("Referência provisória exige rótulo e chave não vazios.")
        return self


EntityReference = Annotated[
    LocalReference | ExternalReference | UnreconciledReference, Field(discriminator="kind")
]
# URI-only payloads from M03.01.02 remain accepted, without guessing locality.
CompatibleReference = ResourceReference | EntityReference


def expect_entity(value: CompatibleReference, expected: EntityType) -> CompatibleReference:
    if not isinstance(value, ResourceReference) and value.entity_type != expected:
        raise ValueError("Tipo de entidade incompatível com a propriedade.")
    return value


WorkReference = Annotated[
    CompatibleReference, AfterValidator(lambda value: expect_entity(value, EntityType.WORK))
]
InstanceReference = Annotated[
    CompatibleReference, AfterValidator(lambda value: expect_entity(value, EntityType.INSTANCE))
]
AgentReference = Annotated[
    CompatibleReference, AfterValidator(lambda value: expect_entity(value, EntityType.AGENT))
]
SubjectReference = Annotated[
    CompatibleReference, AfterValidator(lambda value: expect_entity(value, EntityType.SUBJECT))
]


def expect_authority(value: CompatibleReference) -> CompatibleReference:
    if not isinstance(value, ResourceReference) and value.entity_type not in {
        EntityType.AGENT,
        EntityType.SUBJECT,
    }:
        raise ValueError("Autoridade relacionada exige Agent ou Subject.")
    return value


AuthorityReference = Annotated[CompatibleReference, AfterValidator(expect_authority)]


class LocalizedText(Contract):
    value: Text
    language: LanguageTag | None = None


def unique_languages(values: list[LocalizedText]) -> list[LocalizedText]:
    languages = [(text.language or "").lower() for text in values]
    if len(languages) != len(set(languages)):
        raise ValueError("Somente um valor por idioma, incluindo o valor sem idioma.")
    return values


RequiredTexts = Annotated[list[LocalizedText], Field(min_length=1)]
UniqueTexts = Annotated[RequiredTexts, AfterValidator(unique_languages)]
RequiredReferences = Annotated[list[ResourceReference], Field(min_length=1)]


class Title(Contract):
    kind: Literal["Title", "VariantTitle"] = "Title"
    main_title: UniqueTexts
    subtitle: list[LocalizedText] = Field(default_factory=list)


def primary_title(values: list[Title]) -> list[Title]:
    if not any(title.kind == "Title" for title in values):
        raise ValueError("Work exige ao menos um título não variante.")
    return values


WorkTitles = Annotated[list[Title], Field(min_length=1), AfterValidator(primary_title)]


class Contribution(Contract):
    agent: AgentReference
    role: RequiredReferences


class PublicationDate(Contract):
    value: Text
    datatype: Literal[
        "http://www.w3.org/2001/XMLSchema#string",
        "http://www.w3.org/2001/XMLSchema#gYear",
        "http://www.w3.org/2001/XMLSchema#date",
    ] = "http://www.w3.org/2001/XMLSchema#string"

    @model_validator(mode="after")
    def check_lexical_form(self) -> "PublicationDate":
        if self.datatype.endswith("#string"):
            return self
        pattern = r"(-?(?:[0-9]{4}|[1-9][0-9]{4,}))"
        if self.datatype.endswith("#date"):
            pattern += r"-([0-9]{2})-([0-9]{2})"
        pattern += r"(Z|[+-](?:0[0-9]|1[0-3]):[0-5][0-9]|[+-]14:00)?"
        match = re.fullmatch(pattern, self.value)
        if match is None or int(match[1]) == 0:
            raise ValueError("Data incompatível com o datatype informado.")
        if self.datatype.endswith("#date"):
            year, month, day = int(match[1]), int(match[2]), int(match[3])
            leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
            days = (31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
            if not 1 <= month <= 12 or not 1 <= day <= days[month - 1]:
                raise ValueError("Data de calendário inválida.")
        return self


class Publication(Contract):
    agent: list[AgentReference] = Field(default_factory=list)
    place: list[ResourceReference] = Field(default_factory=list)
    date: list[PublicationDate] = Field(default_factory=list)


class Identifier(Contract):
    kind: Literal["Identifier", "Local", "Isbn"] = "Identifier"
    value: Text
    source: list[ResourceReference] = Field(default_factory=list)


def local_identifier(values: list[Identifier]) -> list[Identifier]:
    if not any(identifier.kind == "Local" for identifier in values):
        raise ValueError("Item exige ao menos um identificador Local.")
    return values


ItemIdentifiers = Annotated[list[Identifier], Field(min_length=1), AfterValidator(local_identifier)]


class Extent(Contract):
    label: RequiredTexts


class Note(Contract):
    label: RequiredTexts
    note_type: list[Text] = Field(default_factory=list)


class Classification(Contract):
    classification_portion: Annotated[list[Text], Field(min_length=1)]
    source: list[ResourceReference] = Field(default_factory=list)


class ShelfMark(Contract):
    value: Text
    source: list[ResourceReference] = Field(default_factory=list)


def disjoint_labels(preferred: list[LocalizedText], alternative: list[LocalizedText]) -> None:
    preferred_terms = {(text.value, (text.language or "").lower()) for text in preferred}
    alternative_terms = {(text.value, (text.language or "").lower()) for text in alternative}
    if preferred_terms & alternative_terms:
        raise ValueError("Rótulos preferidos e alternativos devem ser disjuntos.")
