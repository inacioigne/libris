"""Pure resolution/selection with trusted, declarative semantic and shape registries."""

import hashlib
import json
from collections.abc import Iterable
from typing import Literal

from pydantic import Field, model_validator

from .profile_contract import (
    IRI,
    Contract,
    DeclarativeField,
    DeclarativeResource,
    Labels,
    Name,
    ProfileDefinition,
    ReferenceValue,
    ResolvedProfile,
    ShapeReference,
    StructuredValue,
    Text,
    TypedValue,
    Version,
)
from .relationships import DEFAULT_REGISTRY, EntityType


class ProfileError(ValueError):
    """Stable domain failure, suitable for the future #22 adapter."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def profile_fingerprint(definition: ProfileDefinition) -> str:
    """Canonical release content; availability is explicit metadata, not interpretation."""
    content = json.dumps(
        definition.model_dump(mode="json", exclude={"status", "replacement"}),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


class NamespaceDefinition(Contract):
    prefix: Name
    iri: IRI
    ontology: IRI
    release: Text | None = None
    status: Literal["supported", "review_required"] = "supported"
    label: Labels | None = None
    description: Labels | None = None
    maintainer: IRI | None = None
    inclusion: IRI | None = None
    approval: Literal["technical", "institutional", "pending"] = "technical"


class ClassDefinition(Contract):
    iri: IRI
    entity: EntityType | None = None
    auxiliary: bool = False
    namespace: Name | None = None
    label: Labels | None = None
    description: Labels | None = None
    status: Literal["supported", "deprecated", "review_required"] = "supported"

    @model_validator(mode="after")
    def classification(self) -> "ClassDefinition":
        if (self.entity is None) != self.auxiliary:
            raise ValueError("Classe é entidade principal ou auxiliar suportado.")
        return self


class PropertyDefinition(Contract):
    iri: IRI
    namespace: Name | None = None
    description: Labels | None = None
    # Source ontology evidence is distinct from the supported Libris application surface.
    ontology_source: IRI | None = None
    sources: tuple[IRI, ...] = Field(min_length=1)
    value_kinds: tuple[
        Literal[
            "text",
            "typed",
            "iri",
            "entity",
            "authority",
            "vocabulary",
            "relationship",
            "structured",
        ],
        ...,
    ] = Field(min_length=1)
    target_classes: tuple[IRI, ...] = ()
    target_entities: tuple[EntityType, ...] = ()
    datatypes: tuple[IRI, ...] = ()
    minimum: int = Field(default=0, ge=0, strict=True)
    maximum: int | None = Field(default=None, ge=1, strict=True)
    derived: bool = False
    status: Literal["supported", "deprecated", "review_required"] = "supported"
    label: Labels

    @model_validator(mode="after")
    def consistent(self) -> "PropertyDefinition":
        if self.maximum is not None and self.minimum > self.maximum:
            raise ValueError("Limites do contrato inconsistentes.")
        for values in (
            self.sources,
            self.value_kinds,
            self.target_classes,
            self.target_entities,
            self.datatypes,
        ):
            if len(set(values)) != len(values):
                raise ValueError("Metadado semântico duplicado.")
        return self


class SemanticRegistry(Contract):
    format_version: Literal["1.0", "1.1"] = "1.0"
    version: Version
    namespaces: tuple[NamespaceDefinition, ...]
    classes: tuple[ClassDefinition, ...]
    properties: tuple[PropertyDefinition, ...]

    @model_validator(mode="after")
    def unique(self) -> "SemanticRegistry":
        for keys in (
            tuple(n.prefix for n in self.namespaces),
            tuple(n.iri for n in self.namespaces),
            tuple(c.iri for c in self.classes),
            tuple(p.iri for p in self.properties),
        ):
            if len(set(keys)) != len(keys):
                raise ValueError("Identificador duplicado no registro semântico.")
        # Prefix overlap is forbidden: an extension cannot claim a parent of BIBFRAME.
        for namespace in self.namespaces:
            if not namespace.iri.endswith(("#", "/", ":")):
                raise ValueError("Namespace deve terminar em /, # ou :.")
            if any(
                other.iri.startswith(namespace.iri)
                for other in self.namespaces
                if other != namespace
            ):
                raise ValueError("Namespaces sobrepostos.")
        known_classes = {c.iri for c in self.classes}
        for namespace in self.namespaces:
            if (namespace.prefix == "bf") != (
                namespace.iri == "http://id.loc.gov/ontologies/bibframe/"
            ):
                raise ValueError("O prefixo bf e o namespace BIBFRAME são reservados.")
            if namespace.prefix == "bf" and namespace.ontology != namespace.iri:
                raise ValueError("Uma extensão não substitui a ontologia BIBFRAME.")
            if self.format_version == "1.1" and not (
                namespace.label
                and namespace.description
                and namespace.maintainer
                and namespace.inclusion
            ):
                raise ValueError("Namespace governado exige descrição, fonte e inclusão.")
        terms: tuple[ClassDefinition | PropertyDefinition, ...] = (*self.classes, *self.properties)
        for term in terms:
            namespace = self.namespace_for(term.iri)
            if term.namespace is not None and term.namespace != namespace.prefix:
                raise ValueError("Namespace do termo diverge de sua IRI.")
            if self.format_version == "1.1" and not (
                term.namespace and term.label and term.description
            ):
                raise ValueError("Termo governado exige namespace, nome e descrição.")
        canonical_entities = {
            "http://id.loc.gov/ontologies/bibframe/" + name: EntityType(
                "Agent" if name in {"Person", "Organization"} else name
            )
            for name in ("Work", "Instance", "Item", "Agent", "Person", "Organization")
        }
        canonical_entities["http://www.w3.org/2004/02/skos/core#Concept"] = EntityType.SUBJECT
        for rdf_class in self.classes:
            expected = canonical_entities.get(rdf_class.iri)
            if rdf_class.entity is not None and expected is None:
                raise ValueError("Classe externa não define nova entidade principal.")
            if expected is not None and rdf_class.entity != expected:
                raise ValueError("A extensão não altera a identidade de uma classe canônica.")
        for prop in self.properties:
            self.namespace_for(prop.iri)
            if not set(prop.sources + prop.target_classes) <= known_classes:
                raise ValueError("Classe não registrada nos metadados da propriedade.")
        return self

    def check_extension_of(self, previous: "SemanticRegistry") -> None:
        """Append terms without redefining historical semantic compatibility contracts."""
        namespaces = {n.iri: n for n in self.namespaces}
        for old in previous.namespaces:
            current = namespaces.get(old.iri)
            if current is None or (current.prefix, current.ontology) != (old.prefix, old.ontology):
                raise ProfileError("semantic_override", "Namespace histórico redefinido/removido.")
        for old_class in previous.classes:
            current_class = next((c for c in self.classes if c.iri == old_class.iri), None)
            if current_class is None or (current_class.entity, current_class.auxiliary) != (
                old_class.entity,
                old_class.auxiliary,
            ):
                raise ProfileError("semantic_override", "Classe histórica redefinida/removida.")
        excluded = {"namespace", "description", "ontology_source", "label", "status"}
        for old_prop in previous.properties:
            current_prop = next((p for p in self.properties if p.iri == old_prop.iri), None)
            if current_prop is None or current_prop.model_dump(exclude=excluded) != (
                old_prop.model_dump(exclude=excluded)
            ):
                raise ProfileError(
                    "semantic_override", "Propriedade histórica redefinida/removida."
                )

    def check_class(self, iri: str) -> ClassDefinition:
        namespace = self.namespace_for(iri)
        rdf_class = next((c for c in self.classes if c.iri == iri), None)
        if rdf_class is None:
            raise ProfileError("unknown_class", "Classe não registrada.")
        if namespace.status != "supported" or namespace.approval == "pending":
            raise ProfileError("extension_review_required", "Namespace exige homologação.")
        if rdf_class.status != "supported":
            raise ProfileError("unsupported_class", "Classe não autorizada para o perfil.")
        return rdf_class

    def namespace_for(self, iri: str) -> NamespaceDefinition:
        namespaces = [n for n in self.namespaces if iri.startswith(n.iri) and iri != n.iri]
        if len(namespaces) != 1:
            raise ProfileError("unknown_namespace", "Namespace não registrado.")
        return namespaces[0]

    def check_field(self, resource: DeclarativeResource, field: DeclarativeField) -> None:
        namespace = self.namespace_for(field.property)
        if namespace.prefix != field.namespace:
            raise ProfileError("namespace_mismatch", "Alias não corresponde à URI da propriedade.")
        if namespace.status != "supported" or namespace.approval == "pending":
            raise ProfileError(
                "extension_review_required", "Ontologia exige homologação/adaptação."
            )
        prop = next((p for p in self.properties if p.iri == field.property), None)
        if prop is None:
            raise ProfileError("unknown_property", "Propriedade não registrada.")
        if prop.status != "supported":
            raise ProfileError("unsupported_property", "Propriedade obsoleta ou exige adaptação.")
        if resource.rdf_class not in prop.sources or field.value.kind not in prop.value_kinds:
            raise ProfileError("incompatible_property", "Propriedade/tipo incompatível com origem.")
        if field.derived != prop.derived:
            raise ProfileError("derived_mismatch", "Derivação deve respeitar contrato canônico.")
        value = field.value
        self.check_class(resource.rdf_class)
        if isinstance(value, (ReferenceValue, StructuredValue)):
            for target in value.target_classes:
                self.check_class(target)
        classes = {c.iri: c for c in self.classes}
        if isinstance(value, (ReferenceValue, StructuredValue)):
            if not set(value.target_classes) <= set(prop.target_classes):
                raise ProfileError("incompatible_target", "Classe de destino não suportada.")
            if isinstance(value, ReferenceValue):
                if not set(value.target_entities) <= set(prop.target_entities):
                    raise ProfileError("incompatible_target", "Entidade de destino incompatível.")
                if any(
                    classes[c].entity not in value.target_entities
                    for c in value.target_classes
                    if classes[c].entity is not None
                ):
                    raise ProfileError(
                        "incompatible_target", "Classe e entidade de destino discordam."
                    )
        if isinstance(value, ReferenceValue) and resource.entity is not None:
            canonical = DEFAULT_REGISTRY.entries.get((resource.entity, field.property))
            if canonical is not None and not set(value.target_entities) <= canonical.targets:
                raise ProfileError(
                    "incompatible_target", "Destino viola contrato de relacionamentos."
                )
            if canonical is not None and any(
                classes[target].entity not in canonical.targets for target in value.target_classes
            ):
                raise ProfileError(
                    "incompatible_target", "Classe viola contrato de relacionamentos."
                )
        if isinstance(value, TypedValue) and not set(value.datatypes) <= set(prop.datatypes):
            raise ProfileError("incompatible_datatype", "Datatype fora do contrato da propriedade.")
        if field.policy.min_count < prop.minimum or (
            prop.maximum is not None
            and (field.policy.max_count is None or field.policy.max_count > prop.maximum)
        ):
            raise ProfileError("domain_constraint", "Política enfraquece limite do contrato.")


class ShapeSetDefinition(Contract):
    id: IRI
    release: Version
    contexts: tuple[Literal["snapshot", "composed"], ...] = Field(min_length=1)
    classes: tuple[IRI, ...] = Field(min_length=1)
    bibliographic_contract: Literal["1.0"] = "1.0"
    property_shapes: tuple[IRI, ...] = ()


class ShapeRegistry(Contract):
    sets: tuple[ShapeSetDefinition, ...]

    @model_validator(mode="after")
    def unique(self) -> "ShapeRegistry":
        if len({(s.id, s.release) for s in self.sets}) != len(self.sets):
            raise ValueError("Release SHACL duplicada.")
        return self

    def get(self, reference: ShapeReference) -> ShapeSetDefinition:
        shape = next(
            (s for s in self.sets if (s.id, s.release) == (reference.id, reference.release)), None
        )
        if shape is None:
            raise ProfileError("unknown_shapes", "Release SHACL desconhecida.")
        if reference.context not in shape.contexts:
            raise ProfileError("incompatible_shapes", "Contexto incompatível com release SHACL.")
        return shape


class ProfileRegistry:
    """In-memory snapshot. Inputs and outputs copied; no database/admin lifecycle promise."""

    def __init__(
        self,
        definitions: Iterable[ProfileDefinition],
        semantics: SemanticRegistry,
        shapes: ShapeRegistry,
        *,
        used_releases: Iterable[str] = (),
        semantics_by_release: dict[str, SemanticRegistry] | None = None,
    ) -> None:
        self._semantics = SemanticRegistry.model_validate_json(semantics.model_dump_json())
        self._semantics_by_release = {
            key: SemanticRegistry.model_validate_json(value.model_dump_json())
            for key, value in (semantics_by_release or {}).items()
        }
        self._shapes = ShapeRegistry.model_validate_json(shapes.model_dump_json())
        self._used = frozenset(used_releases)
        self._definitions: dict[str, ProfileDefinition] = {}
        family_versions: set[tuple[str, str]] = set()
        for definition in definitions:
            definition = ProfileDefinition.model_validate_json(definition.model_dump_json())
            key = (definition.id, definition.release)
            if definition.release_id in self._definitions or key in family_versions:
                raise ProfileError("duplicate_release", "Release/versão da família duplicada.")
            family_versions.add(key)
            self._definitions[definition.release_id] = definition
        if not self._used <= self._definitions.keys():
            raise ProfileError("unknown_release", "Release histórica não registrada.")
        if not self._semantics_by_release.keys() <= self._definitions.keys():
            raise ProfileError("unknown_release", "Registro associado a perfil desconhecido.")
        # Validate all compositions before making this registry available.
        for release_id in self._definitions:
            self._resolve(release_id, ())
            successors: set[str] = set()
            current: str | None = release_id
            while current:
                if current in successors:
                    raise ProfileError("replacement_cycle", "Ciclo de substituição de releases.")
                successors.add(current)
                current = self.definition(current).replacement

    def semantic_registry_for(self, release_id: str) -> SemanticRegistry:
        """An explicit association overrides the inherited registry, never historical releases."""
        definition = self.definition(release_id)
        registry = self._semantics_by_release.get(release_id)
        if registry is None and definition.base_release:
            return self.semantic_registry_for(definition.base_release)
        return SemanticRegistry.model_validate_json((registry or self._semantics).model_dump_json())

    def release_ids(self) -> tuple[str, ...]:
        """Identificadores estáveis, sem expor armazenamento ou estado mutável."""
        return tuple(sorted(self._definitions))

    def definition(self, release_id: str) -> ProfileDefinition:
        try:
            return ProfileDefinition.model_validate_json(
                self._definitions[release_id].model_dump_json()
            )
        except KeyError as error:
            raise ProfileError("unknown_release", "Release de perfil inexistente.") from error

    def resolve(self, release_id: str) -> ResolvedProfile:
        return self._resolve(release_id, ())

    def _resolve(self, release_id: str, trail: tuple[str, ...]) -> ResolvedProfile:
        if release_id in trail:
            raise ProfileError("composition_cycle", "Dependência cíclica de perfis.")
        definition = self.definition(release_id)
        parent = (
            self._resolve(definition.base_release, (*trail, release_id))
            if definition.base_release
            else None
        )
        if parent and (
            not set(definition.applies_to) <= set(parent.applies_to)
            or definition.bibliographic_contract != parent.bibliographic_contract
            or definition.purpose != parent.purpose
            or (parent.institution and definition.institution != parent.institution)
            or (
                parent.resource_types
                and (
                    not definition.resource_types
                    or not set(definition.resource_types) <= set(parent.resource_types)
                )
            )
        ):
            raise ProfileError("incompatible_base", "Especialização incompatível com perfil base.")
        if definition.replacement:
            replacement = self.definition(definition.replacement)
            if replacement.id != definition.id:
                raise ProfileError(
                    "incompatible_replacement", "Sucessora deve pertencer à família."
                )
        resources = {r.rdf_class: r for r in parent.resources} if parent else {}
        for resource in definition.resources:
            if resource.rdf_class in resources:
                resource = self._merge_resource(resources[resource.rdf_class], resource)
            elif any(field.overrides for field in resource.fields):
                raise ProfileError("missing_override", "Sobrescrita sem campo base.")
            resources[resource.rdf_class] = DeclarativeResource.model_validate(
                {
                    **resource.model_dump(),
                    "fields": tuple(
                        sorted(resource.fields, key=lambda f: (f.presentation.order, f.name))
                    ),
                    "sections": tuple(
                        sorted(resource.sections, key=lambda section: (section.order, section.id))
                    ),
                    "groups": tuple(
                        sorted(resource.groups, key=lambda group: (group.order, group.id))
                    ),
                }
            )
        references = {(r.id, r.context): r for r in parent.validation} if parent else {}
        for reference in definition.validation:
            key = (reference.id, reference.context)
            if key in references and references[key] != reference:
                raise ProfileError(
                    "shape_conflict", "Especialização não troca release SHACL herdada."
                )
            references[key] = reference
        metadata = definition.model_dump(
            exclude={"format", "format_version", "base_release", "resources", "validation"}
        )
        resolved = ResolvedProfile.model_validate(
            {
                **metadata,
                "lineage": (*parent.lineage, release_id) if parent else (release_id,),
                "resources": tuple(resources[k] for k in sorted(resources)),
                "validation": tuple(references[k] for k in sorted(references)),
            }
        )
        self._check_resolved(resolved)
        return resolved

    def _merge_resource(
        self, parent: DeclarativeResource, child: DeclarativeResource
    ) -> DeclarativeResource:
        if parent.entity != child.entity:
            raise ProfileError("incompatible_entity", "Especialização não muda entidade da classe.")
        fields = {f.name: f for f in parent.fields}
        for field in child.fields:
            existing = fields.get(field.name)
            if existing is None:
                if field.overrides:
                    raise ProfileError("missing_override", "Campo herdado não encontrado.")
                if any(other.property == field.property for other in fields.values()):
                    raise ProfileError(
                        "property_conflict", "Mesmo predicado com identificador diferente."
                    )
            else:
                if not field.overrides:
                    raise ProfileError("field_conflict", "Sobrescrita deve ser explícita.")
                if (
                    existing.property,
                    existing.namespace,
                    existing.value,
                    existing.derived,
                    existing.validation,
                ) != (
                    field.property,
                    field.namespace,
                    field.value,
                    field.derived,
                    field.validation,
                ):
                    raise ProfileError(
                        "semantic_override", "Sobrescrita altera significado semântico."
                    )
                if existing.policy != field.policy:
                    if (
                        not existing.policy.specializable
                        or field.policy.specializable != existing.policy.specializable
                    ):
                        raise ProfileError(
                            "policy_override", "Regra catalográfica não autoriza especialização."
                        )
                    if (
                        field.policy.min_count < existing.policy.min_count
                        or (
                            existing.policy.max_count is not None
                            and (
                                field.policy.max_count is None
                                or field.policy.max_count > existing.policy.max_count
                            )
                        )
                        or (existing.policy.required and not field.policy.required)
                        or (
                            existing.policy.allowed_values
                            and not set(v.model_dump_json() for v in field.policy.allowed_values)
                            <= set(v.model_dump_json() for v in existing.policy.allowed_values)
                        )
                        or (existing.policy.allowed_values and not field.policy.allowed_values)
                    ):
                        raise ProfileError(
                            "policy_relaxation", "Especialização só pode restringir política."
                        )
            fields[field.name] = DeclarativeField.model_validate(
                {**field.model_dump(), "overrides": False}
            )
        sections = {s.id: s for s in parent.sections}
        sections.update({s.id: s for s in child.sections})
        groups = {g.id: g for g in parent.groups}
        groups.update({g.id: g for g in child.groups})
        return DeclarativeResource.model_validate(
            {
                **child.model_dump(),
                "fields": tuple(
                    sorted(fields.values(), key=lambda f: (f.presentation.order, f.name))
                ),
                "sections": tuple(sorted(sections.values(), key=lambda s: (s.order, s.id))),
                "groups": tuple(sorted(groups.values(), key=lambda g: (g.order, g.id))),
            }
        )

    def _check_resolved(self, profile: ResolvedProfile) -> None:
        semantics = self.semantic_registry_for(profile.release_id)
        classes = {c.iri: c for c in semantics.classes}
        resources = {r.rdf_class: r for r in profile.resources}
        entities = {r.entity for r in profile.resources if r.entity}
        if not set(profile.applies_to) <= entities:
            raise ProfileError(
                "missing_entity", "Perfil não descreve todas as entidades aplicáveis."
            )
        if not profile.validation:
            raise ProfileError(
                "missing_shapes", "Perfil resolvido exige associação SHACL explícita."
            )
        for resource in profile.resources:
            rdf_class = classes.get(resource.rdf_class)
            if rdf_class is None or rdf_class.entity != resource.entity:
                raise ProfileError("incompatible_class", "Classe/entidade fora do modelo canônico.")
            semantics.check_class(resource.rdf_class)
        shape_sets = [self._shapes.get(reference) for reference in profile.validation]
        covered = {c for s in shape_sets for c in s.classes}
        if not set(resources) <= covered:
            raise ProfileError("incompatible_shapes", "SHACL não cobre classes declaradas.")
        self._check_structures(resources)
        for resource in profile.resources:
            names = {f.name: f for f in resource.fields}
            sections = {s.id for s in resource.sections}
            groups = {g.id: g for g in resource.groups}
            if not resource.fields:
                raise ProfileError("empty_resource", "Recurso resolvido sem campos.")
            if any(g.section not in sections for g in resource.groups):
                raise ProfileError("unknown_section", "Grupo com seção inexistente.")
            for field in resource.fields:
                semantics.check_field(resource, field)
                presentation = field.presentation
                if presentation.section and presentation.section not in sections:
                    raise ProfileError("unknown_section", "Seção do campo inexistente.")
                if presentation.group and (
                    presentation.group not in groups
                    or (groups[presentation.group].section != presentation.section)
                ):
                    raise ProfileError("unknown_group", "Grupo do campo incompatível.")
                if isinstance(field.value, StructuredValue):
                    if not set(field.value.target_classes) <= resources.keys():
                        raise ProfileError(
                            "missing_structure", "Classe auxiliar sem definição de edição."
                        )
                    if any(not classes[c].auxiliary for c in field.value.target_classes):
                        raise ProfileError(
                            "embedded_entity", "Entidade persistente não é auxiliar privado."
                        )
                for constraint in field.validation:
                    matched = [
                        s
                        for s in shape_sets
                        if (s.id, s.release) == (constraint.shape_id, constraint.shape_release)
                    ]
                    if (
                        not matched
                        or resource.rdf_class not in matched[0].classes
                        or (
                            constraint.property_shape
                            and constraint.property_shape not in matched[0].property_shapes
                        )
                    ):
                        raise ProfileError(
                            "unknown_constraint", "Restrição SHACL não associada ao perfil."
                        )
                for condition in presentation.conditions:
                    dependency = names.get(condition.field)
                    if dependency is None or condition.field == field.name:
                        raise ProfileError(
                            "unknown_dependency", "Dependência inexistente ou autorreferência."
                        )
                    if condition.value:
                        dependency.check_value(condition.value)
            self._check_conditions(names)

    @staticmethod
    def _check_structures(resources: dict[str, DeclarativeResource]) -> None:
        def visit(rdf_class: str, trail: tuple[str, ...]) -> None:
            if rdf_class in trail:
                raise ProfileError("structure_cycle", "Ciclo de estruturas auxiliares.")
            if rdf_class not in resources:
                raise ProfileError("missing_structure", "Classe auxiliar sem definição de edição.")
            for field in resources[rdf_class].fields:
                if isinstance(field.value, StructuredValue):
                    for target in field.value.target_classes:
                        visit(target, (*trail, rdf_class))

        for rdf_class in resources:
            visit(rdf_class, ())

    @staticmethod
    def _check_conditions(fields: dict[str, DeclarativeField]) -> None:
        def visit(name: str, trail: tuple[str, ...]) -> None:
            if name in trail:
                raise ProfileError("condition_cycle", "Ciclo de dependências condicionais.")
            for condition in fields[name].presentation.conditions:
                visit(condition.field, (*trail, name))

        for name in fields:
            visit(name, ())

    def candidates(
        self,
        entity: EntityType,
        *,
        resource_type: str | None = None,
        purpose: str = "cataloging",
        institution: str | None = None,
        statuses: tuple[str, ...] = ("published",),
    ) -> tuple[ResolvedProfile, ...]:
        candidates = [
            self.resolve(d.release_id)
            for d in self._definitions.values()
            if entity in d.applies_to
            and d.status in statuses
            and d.purpose == purpose
            and (not d.resource_types or resource_type in d.resource_types)
            and (d.institution is None or d.institution == institution)
        ]
        return tuple(
            sorted(
                candidates,
                key=lambda p: (
                    -int(p.institution is not None),
                    -int(bool(p.resource_types)),
                    -p.priority,
                    -len(p.lineage),
                    p.id,
                    tuple(-int(n) for n in p.release.split(".")),
                    p.release_id,
                ),
            )
        )

    def select(
        self,
        entity: EntityType,
        *,
        release_id: str | None = None,
        resource_type: str | None = None,
        purpose: str = "cataloging",
        institution: str | None = None,
        statuses: tuple[str, ...] = ("published",),
    ) -> ResolvedProfile:
        if release_id:
            profile = self.resolve(release_id)
            if (
                entity not in profile.applies_to
                or profile.status not in statuses
                or profile.purpose != purpose
                or (profile.resource_types and resource_type not in profile.resource_types)
                or (profile.institution and profile.institution != institution)
            ):
                raise ProfileError(
                    "inapplicable_profile", "Release solicitada não é aplicável/ativa."
                )
            return profile
        candidates = self.candidates(
            entity,
            resource_type=resource_type,
            purpose=purpose,
            institution=institution,
            statuses=statuses,
        )
        if not candidates:
            raise ProfileError("no_profile", "Nenhum perfil aplicável.")
        return candidates[0]

    def add_release(self, definition: ProfileDefinition) -> "ProfileRegistry":
        return ProfileRegistry(
            (*self._definitions.values(), definition),
            self._semantics,
            self._shapes,
            used_releases=self._used,
            semantics_by_release=self._semantics_by_release,
        )

    def transition_release(
        self,
        release_id: str,
        status: Literal["candidate", "published", "deprecated"],
        *,
        replacement: str | None = None,
    ) -> "ProfileRegistry":
        """Explicit availability transition; a new registry snapshot, never semantic edits."""
        old = self.definition(release_id)
        allowed = {
            "draft": {"candidate"},
            "candidate": {"published", "deprecated"},
            "published": {"deprecated"},
            "deprecated": set(),
        }
        if status not in allowed[old.status] or (replacement and status != "deprecated"):
            raise ProfileError("invalid_transition", "Transição de disponibilidade inválida.")
        incoming = ProfileDefinition.model_validate(
            {**old.model_dump(), "status": status, "replacement": replacement}
        )
        return ProfileRegistry(
            (incoming if d.release_id == release_id else d for d in self._definitions.values()),
            self._semantics,
            self._shapes,
            used_releases=self._used,
            semantics_by_release=self._semantics_by_release,
        )

    def replace_draft(self, definition: ProfileDefinition) -> "ProfileRegistry":
        old = self.definition(definition.release_id)
        if old == definition:
            return self
        if old.status != "draft" or old.release_id in self._used:
            raise ProfileError(
                "immutable_release", "Release publicada/candidata/histórica é imutável."
            )
        if (old.id, old.release) != (definition.id, definition.release):
            raise ProfileError("identity_change", "Identidade da release não pode mudar.")
        # A draft that is a dependency is also pinned by descendants.
        if any(d.base_release == old.release_id for d in self._definitions.values()):
            raise ProfileError("immutable_dependency", "Release base já fixada em composição.")
        return ProfileRegistry(
            (
                definition if d.release_id == old.release_id else d
                for d in self._definitions.values()
            ),
            self._semantics,
            self._shapes,
            used_releases=self._used,
            semantics_by_release=self._semantics_by_release,
        )


class CompatibilityChange(Contract):
    path: str
    compatible: bool
    reason: str


def compare_profiles(old: ResolvedProfile, new: ResolvedProfile) -> tuple[CompatibilityChange, ...]:
    """Conservative read/editor compatibility; never migrates RDF or revisions."""
    changes: list[CompatibilityChange] = []
    if (
        old.id,
        old.bibliographic_contract,
        old.applies_to,
        old.resource_types,
        old.purpose,
        old.institution,
    ) != (
        new.id,
        new.bibliographic_contract,
        new.applies_to,
        new.resource_types,
        new.purpose,
        new.institution,
    ):
        changes.append(
            CompatibilityChange(
                path="metadata", compatible=False, reason="Aplicabilidade/contrato alterado."
            )
        )
    if old.validation != new.validation:
        changes.append(
            CompatibilityChange(
                path="validation",
                compatible=False,
                reason="Associação SHACL alterada; exige revisão explícita.",
            )
        )
    if old.status != new.status:
        changes.append(
            CompatibilityChange(
                path="status",
                compatible=new.status != "deprecated",
                reason="Estado de ciclo de vida alterado.",
            )
        )
    before = {(r.rdf_class, f.name): f for r in old.resources for f in r.fields}
    after = {(r.rdf_class, f.name): f for r in new.resources for f in r.fields}
    for key in sorted(before.keys() | after.keys()):
        previous, current = before.get(key), after.get(key)
        path = "/".join(key)
        if previous is None and current is not None:
            changes.append(
                CompatibilityChange(
                    path=path, compatible=current.policy.min_count == 0, reason="Campo adicionado."
                )
            )
        elif current is None:
            changes.append(
                CompatibilityChange(path=path, compatible=False, reason="Campo removido.")
            )
        elif previous is not None and previous != current:
            # All policy edits are conservatively breaking; visual/translated text edits are safe.
            compatible = (
                previous.property,
                previous.namespace,
                previous.value,
                previous.policy,
                previous.derived,
                previous.validation,
            ) == (
                current.property,
                current.namespace,
                current.value,
                current.policy,
                current.derived,
                current.validation,
            )
            changes.append(
                CompatibilityChange(
                    path=path,
                    compatible=compatible,
                    reason="Apresentação/rótulo ou contrato do campo alterado.",
                )
            )
    before_layout = tuple((r.rdf_class, r.sections, r.groups) for r in old.resources)
    after_layout = tuple((r.rdf_class, r.sections, r.groups) for r in new.resources)
    if before_layout != after_layout:
        changes.append(
            CompatibilityChange(
                path="layout", compatible=True, reason="Organização de seções/grupos alterada."
            )
        )
    return tuple(changes)
