"""Declarative form contract v2; configuration over RDF, never a record/store."""

import re
from datetime import date
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

from .iris import validate_iri
from .relationships import EntityType

IRI = Annotated[str, Field(strict=True), AfterValidator(validate_iri)]
Name = Annotated[str, Field(pattern=r"^[A-Za-z][A-Za-z0-9_-]*$", strict=True)]
Text = Annotated[str, Field(min_length=1, strict=True)]
Version = Annotated[str, Field(pattern=r"^[0-9]+\.[0-9]+(?:\.[0-9]+)?$", strict=True)]
Language = Annotated[str, Field(pattern=r"^[a-zA-Z]+(?:-[a-zA-Z0-9]+)*$", strict=True)]
Labels = Annotated[dict[Language, Text], Field(min_length=1)]
XSD = "http://www.w3.org/2001/XMLSchema#"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
DATATYPES = frozenset(
    XSD + name
    for name in ("string", "integer", "decimal", "double", "boolean", "date", "dateTime", "gYear")
)


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True)


class LanguagePolicy(Contract):
    enabled: bool = False
    required: bool = False
    allowed: tuple[Language, ...] = ()
    unique: bool = False

    @model_validator(mode="after")
    def consistent(self) -> "LanguagePolicy":
        if not self.enabled and (self.required or self.allowed or self.unique):
            raise ValueError("Configuração de idioma exige enabled.")
        if len({language.lower() for language in self.allowed}) != len(self.allowed):
            raise ValueError("Idioma duplicado.")
        return self


class TextValue(Contract):
    kind: Literal["text"]
    node_kind: Literal["Literal"] = "Literal"
    language: LanguagePolicy = Field(default_factory=LanguagePolicy)


class TypedValue(Contract):
    kind: Literal["typed"]
    node_kind: Literal["Literal"] = "Literal"
    datatypes: tuple[IRI, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def supported(self) -> "TypedValue":
        if len(set(self.datatypes)) != len(self.datatypes) or not set(self.datatypes) <= DATATYPES:
            raise ValueError("Datatype não suportado ou duplicado.")
        return self


class ReferenceValue(Contract):
    kind: Literal["iri", "entity", "authority", "vocabulary", "relationship"]
    node_kind: Literal["IRI"] = "IRI"
    target_entities: tuple[EntityType, ...] = ()
    target_classes: tuple[IRI, ...] = ()
    vocabulary: IRI | None = None
    authority: IRI | None = None

    @model_validator(mode="after")
    def consistent(self) -> "ReferenceValue":
        if self.kind in {"entity", "authority", "relationship"} and not self.target_entities:
            raise ValueError("Referência a entidade exige tipos de destino.")
        if self.kind == "authority" and (
            self.authority is None
            or not set(self.target_entities) <= {EntityType.AGENT, EntityType.SUBJECT}
        ):
            raise ValueError("Autoridade exige fonte e destinos Agent/Subject.")
        if self.kind == "vocabulary" and self.vocabulary is None:
            raise ValueError("Vocabulário exige URI da fonte.")
        if self.authority is not None and self.kind != "authority":
            raise ValueError("Fonte de autoridade pertence à variante authority.")
        for values in (self.target_entities, self.target_classes):
            if len(set(values)) != len(values):
                raise ValueError("Destino duplicado.")
        return self


class StructuredValue(Contract):
    kind: Literal["structured"]
    node_kind: Literal["BlankNodeOrIRI"] = "BlankNodeOrIRI"
    target_classes: tuple[IRI, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique(self) -> "StructuredValue":
        if len(set(self.target_classes)) != len(self.target_classes):
            raise ValueError("Classe de destino duplicada.")
        return self


ValueDefinition = Annotated[
    TextValue | TypedValue | ReferenceValue | StructuredValue, Field(discriminator="kind")
]


class LiteralDefault(Contract):
    kind: Literal["literal"]
    value: Text
    language: Language | None = None
    datatype: IRI | None = None

    @model_validator(mode="after")
    def exclusive(self) -> "LiteralDefault":
        if self.language is not None and self.datatype is not None:
            raise ValueError("Literal com idioma não recebe datatype explícito.")
        return self


class IRIDefault(Contract):
    kind: Literal["iri"]
    iri: IRI


DefaultValue = Annotated[LiteralDefault | IRIDefault, Field(discriminator="kind")]


def valid_lexical(value: str, datatype: str) -> bool:
    """Supported default lexicals; no coercion, normalization or remote datatype lookup."""
    local = datatype.removeprefix(XSD)
    if local == "string":
        return True
    if local == "boolean":
        return value in {"true", "false", "0", "1"}
    if local == "integer":
        return re.fullmatch(r"[+-]?[0-9]+", value) is not None
    if local == "decimal":
        return re.fullmatch(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)", value) is not None
    if local == "double":
        return (
            re.fullmatch(
                r"(?:[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?|INF|-INF|NaN)",
                value,
            )
            is not None
        )
    # Defaults intentionally support Gregorian years 0001..9999 only.
    timezone = r"(?:Z|[+-](?:(?:0[0-9]|1[0-3]):[0-5][0-9]|14:00))?"
    if local == "gYear":
        return re.fullmatch(r"[0-9]{4}" + timezone, value) is not None and value[:4] != "0000"
    if local in {"date", "dateTime"}:
        suffix = (
            "" if local == "date" else r"T(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9](?:\.[0-9]+)?"
        )
        if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}" + suffix + timezone, value) is None:
            return False
        try:
            date.fromisoformat(value[:10])
        except ValueError:
            return False
        return True
    return False


class CatalogPolicy(Contract):
    min_count: int = Field(default=0, ge=0, strict=True)
    max_count: int | None = Field(default=None, ge=1, strict=True)
    repeatable: bool = True
    required: bool = False
    allowed_values: tuple[DefaultValue, ...] = ()
    default: DefaultValue | None = None
    specializable: bool = False

    @model_validator(mode="after")
    def cardinality(self) -> "CatalogPolicy":
        if self.max_count is not None and self.min_count > self.max_count:
            raise ValueError("Cardinalidade mínima excede máxima.")
        if self.repeatable != (self.max_count != 1):
            raise ValueError("Repetibilidade incompatível com cardinalidade.")
        if self.required != (self.min_count > 0):
            raise ValueError("Política catalográfica obrigatória exige mínimo positivo.")
        if len({v.model_dump_json() for v in self.allowed_values}) != len(self.allowed_values):
            raise ValueError("Valor controlado duplicado.")
        if self.default and self.allowed_values and self.default not in self.allowed_values:
            raise ValueError("Default fora dos valores controlados.")
        return self


class Condition(Contract):
    field: Name
    operator: Literal["present", "absent", "equals"]
    value: DefaultValue | None = None
    effect: Literal["visible", "editable", "required"]

    @model_validator(mode="after")
    def operand(self) -> "Condition":
        if (self.operator == "equals") != (self.value is not None):
            raise ValueError("Somente equals exige valor na condição.")
        return self


class Presentation(Contract):
    input: Literal[
        "text", "textarea", "number", "boolean", "date", "select", "reference", "structured"
    ] = "text"
    order: int = Field(default=0, ge=0, strict=True)
    section: Name | None = None
    group: Name | None = None
    visible: bool = True
    editable: bool = True
    required_in_form: bool = False
    help: dict[Language, Text] = Field(default_factory=dict)
    conditions: tuple[Condition, ...] = ()


class ShapeReference(Contract):
    id: IRI
    release: Version
    context: Literal["snapshot", "composed"] = "snapshot"


class FieldConstraint(Contract):
    shape_id: IRI
    shape_release: Version
    property_shape: IRI | None = None


class DeclarativeField(Contract):
    name: Name
    property: IRI
    namespace: Name
    label: Labels
    description: dict[Language, Text] = Field(default_factory=dict)
    value: ValueDefinition
    policy: CatalogPolicy = Field(default_factory=CatalogPolicy)
    presentation: Presentation = Field(default_factory=Presentation)
    derived: bool = False
    validation: tuple[FieldConstraint, ...] = ()
    overrides: bool = False

    def check_value(self, value: DefaultValue) -> None:
        if isinstance(self.value, StructuredValue):
            raise ValueError("Auxiliar estruturado não admite default/enum escalar.")
        if isinstance(self.value, ReferenceValue):
            if not isinstance(value, IRIDefault):
                raise ValueError("Referência exige valor IRI.")
        elif not isinstance(value, LiteralDefault):
            raise ValueError("Campo literal exige valor literal.")
        elif isinstance(self.value, TextValue):
            language = self.value.language
            if value.datatype not in {None, XSD + "string"}:
                raise ValueError("Texto exige datatype textual.")
            if value.language and (
                not language.enabled
                or (
                    language.allowed
                    and value.language.lower()
                    not in {allowed.lower() for allowed in language.allowed}
                )
            ):
                raise ValueError("Idioma do valor não permitido.")
            if language.required and not value.language:
                raise ValueError("Valor exige idioma.")
        elif isinstance(self.value, TypedValue):
            if (
                value.language
                or value.datatype not in self.value.datatypes
                or not valid_lexical(value.value, value.datatype or "")
            ):
                raise ValueError("Default/enum incompatível com datatype.")

    @model_validator(mode="after")
    def coherent(self) -> "DeclarativeField":
        for value in (
            *self.policy.allowed_values,
            *((self.policy.default,) if self.policy.default else ()),
        ):
            self.check_value(value)
        if self.derived and (self.presentation.editable or self.policy.default is not None):
            raise ValueError("Propriedade derivada é somente leitura e não recebe default.")
        control = self.presentation.input
        if isinstance(self.value, StructuredValue) and control != "structured":
            raise ValueError("Auxiliar exige controle structured.")
        if isinstance(self.value, ReferenceValue) and control not in {"reference", "select"}:
            raise ValueError("Referência exige controle reference/select.")
        if isinstance(self.value, TextValue) and control not in {"text", "textarea", "select"}:
            raise ValueError("Texto exige controle textual/select.")
        if isinstance(self.value, TypedValue):
            permitted = {
                "number": {XSD + name for name in ("integer", "decimal", "double")},
                "boolean": {XSD + "boolean"},
                "date": {XSD + name for name in ("date", "dateTime", "gYear")},
            }
            if control not in {"text", "select"} and not set(self.value.datatypes) <= permitted.get(
                control, set()
            ):
                raise ValueError("Controle incompatível com datatype.")
        if (
            control == "select"
            and not self.policy.allowed_values
            and not (
                isinstance(self.value, ReferenceValue)
                and (self.value.vocabulary or self.value.authority)
            )
        ):
            raise ValueError("Seleção exige valores controlados ou fonte.")
        return self


class Section(Contract):
    id: Name
    label: Labels
    order: int = Field(default=0, ge=0, strict=True)


class Group(Section):
    section: Name


class DeclarativeResource(Contract):
    rdf_class: IRI
    entity: EntityType | None = None
    label: Labels
    sections: tuple[Section, ...] = ()
    groups: tuple[Group, ...] = ()
    fields: tuple[DeclarativeField, ...] = ()

    @model_validator(mode="after")
    def unique(self) -> "DeclarativeResource":
        for values in (
            tuple(field.name for field in self.fields),
            tuple(field.property for field in self.fields),
            tuple(section.id for section in self.sections),
            tuple(group.id for group in self.groups),
        ):
            if len(set(values)) != len(values):
                raise ValueError("Identificador/propriedade duplicado no recurso.")
        return self


class ProfileMetadata(Contract):
    id: IRI
    release_id: IRI
    release: Version
    bibliographic_contract: Literal["1.0"] = "1.0"
    status: Literal["draft", "candidate", "published", "deprecated"]
    category: Literal["system", "institutional", "specialization"]
    label: Labels
    description: Labels
    applies_to: tuple[EntityType, ...] = Field(min_length=1)
    resource_types: tuple[IRI, ...] = ()
    purpose: Name = "cataloging"
    institution: IRI | None = None
    priority: int = Field(default=0, ge=0, strict=True)
    replacement: IRI | None = None

    @model_validator(mode="after")
    def metadata(self) -> "ProfileMetadata":
        if self.id == self.release_id:
            raise ValueError("Família e release exigem identidades distintas no formato 2.0.")
        if len(set(self.applies_to)) != len(self.applies_to):
            raise ValueError("Entidade duplicada.")
        if len(set(self.resource_types)) != len(self.resource_types):
            raise ValueError("Tipo documental duplicado.")
        if self.category == "institutional" and not self.institution:
            raise ValueError("Perfil institucional exige contexto institucional.")
        if self.replacement == self.release_id:
            raise ValueError("Release não substitui a si própria.")
        if self.replacement and self.status != "deprecated":
            raise ValueError("Substituição exige estado deprecated.")
        return self


class ProfileDefinition(ProfileMetadata):
    model_config = ConfigDict(
        json_schema_extra={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "urn:libris:schema:catalog-profile:2.0",
        }
    )
    format: Literal["libris.catalog-profile"] = "libris.catalog-profile"
    format_version: Literal["2.0"] = "2.0"
    base_release: IRI | None = None
    validation: tuple[ShapeReference, ...] = ()
    resources: tuple[DeclarativeResource, ...] = ()

    @model_validator(mode="after")
    def declaration(self) -> "ProfileDefinition":
        if not self.base_release and not self.resources:
            raise ValueError("Perfil base exige recursos.")
        if self.category == "specialization" and self.base_release is None:
            raise ValueError("Especialização exige release base.")
        if len({r.rdf_class for r in self.resources}) != len(self.resources):
            raise ValueError("Classe duplicada no perfil.")
        keys = [(r.id, r.context) for r in self.validation]
        if len(set(keys)) != len(keys):
            raise ValueError("Conjunto SHACL duplicado por contexto.")
        return self


class ResolvedProfile(ProfileMetadata):
    model_config = ConfigDict(
        json_schema_extra={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "urn:libris:schema:resolved-profile:2.0",
        }
    )
    format: Literal["libris.resolved-profile"] = "libris.resolved-profile"
    format_version: Literal["2.0"] = "2.0"
    lineage: tuple[IRI, ...]
    validation: tuple[ShapeReference, ...]
    resources: tuple[DeclarativeResource, ...]

    def fields_for_path(self, path: str | None, *, rdf_class: str | None = None) -> tuple[str, ...]:
        """Qualified IDs; unknown/complex paths remain report-level issues."""
        return tuple(
            f"{resource.rdf_class}/{field.name}"
            for resource in self.resources
            if rdf_class is None or resource.rdf_class == rdf_class
            for field in resource.fields
            if field.property == path
        )


class SnapshotReference(Contract):
    uri: IRI
    revision: int = Field(ge=1, strict=True)
    profile_release: IRI


class ProfileValidationContext(Contract):
    profile_release: IRI
    mode: Literal["snapshot", "composed"] = "snapshot"
    snapshots: tuple[SnapshotReference, ...] = ()

    @model_validator(mode="after")
    def snapshot_count(self) -> "ProfileValidationContext":
        if self.mode == "snapshot" and len(self.snapshots) > 1:
            raise ValueError("Modo snapshot aceita somente uma revisão proprietária.")
        if len({s.uri for s in self.snapshots}) != len(self.snapshots):
            raise ValueError("Composição não aceita duas revisões da mesma entidade.")
        return self
