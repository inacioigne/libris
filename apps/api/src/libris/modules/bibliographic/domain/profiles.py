"""Local form descriptors; SHACL remains the semantic validator."""

from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def absolute_iri(value: str) -> str:
    if not urlsplit(value).scheme or any(character.isspace() for character in value):
        raise ValueError("O descritor deve usar uma IRI absoluta sem espaços.")
    return value


class ProfileField(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: str = Field(min_length=1)
    property: str
    label: dict[str, str] = Field(min_length=1)
    value_kind: Literal["literal", "resource"] = Field(alias="valueKind")
    node_kind: Literal["IRI", "Literal", "BlankNodeOrIRI"] = Field(alias="nodeKind")
    min_count: int = Field(ge=0, alias="minCount")
    max_count: int | None = Field(default=None, ge=1, alias="maxCount")
    repeatable: bool
    required_in_form: bool = Field(alias="requiredInForm")
    languages: bool = False
    datatypes: list[str] = Field(default_factory=list)
    target_classes: list[str] = Field(default_factory=list, alias="targetClasses")
    vocabulary: str | None = None
    derived: bool = False
    absent: Literal["omit", "violation"]
    validation: str

    @field_validator("property")
    @classmethod
    def check_property(cls, value: str) -> str:
        return absolute_iri(value)

    @model_validator(mode="after")
    def check_cardinality(self) -> "ProfileField":
        if self.max_count is not None and self.min_count > self.max_count:
            raise ValueError("Cardinalidade mínima excede a máxima.")
        if self.repeatable != (self.max_count != 1):
            raise ValueError("Repetibilidade deve corresponder à cardinalidade.")
        if self.required_in_form != (self.min_count > 0):
            raise ValueError("Obrigatoriedade deve corresponder à cardinalidade.")
        if self.absent != ("violation" if self.min_count else "omit"):
            raise ValueError("Política de ausência incompatível.")
        if (self.value_kind == "literal") != (self.node_kind == "Literal"):
            raise ValueError("Tipo do campo incompatível com o nó RDF.")
        if self.value_kind == "resource" and (self.languages or self.datatypes):
            raise ValueError("Idioma/datatype pertencem a campos literais.")
        if self.value_kind == "literal" and self.target_classes:
            raise ValueError("Classe de destino pertence a campos de recurso.")
        for iri in self.target_classes + self.datatypes:
            absolute_iri(iri)
        if self.vocabulary is not None:
            absolute_iri(self.vocabulary)
        return self


class ProfileResource(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    rdf_class: str = Field(alias="class")
    label: dict[str, str] = Field(min_length=1)
    fields: list[ProfileField] = Field(min_length=1)

    @field_validator("rdf_class")
    @classmethod
    def check_class(cls, value: str) -> str:
        return absolute_iri(value)

    @model_validator(mode="after")
    def check_fields(self) -> "ProfileResource":
        if len({field.property for field in self.fields}) != len(self.fields):
            raise ValueError("Propriedade duplicada no mesmo recurso.")
        return self


class CatalogProfile(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: str
    version: int = Field(ge=1)
    release: str
    status: Literal["candidate"]
    label: dict[str, str] = Field(min_length=1)
    validation_shapes: str = Field(alias="validationShapes")
    resources: list[ProfileResource] = Field(min_length=1)

    @field_validator("id")
    @classmethod
    def check_identity(cls, value: str) -> str:
        return absolute_iri(value)

    @model_validator(mode="after")
    def check_resources(self) -> "CatalogProfile":
        if len({resource.rdf_class for resource in self.resources}) != len(self.resources):
            raise ValueError("Classe duplicada no perfil.")
        return self
