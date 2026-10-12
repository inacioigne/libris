"""Read package-owned profile artifacts only; callers cannot supply paths or URLs."""

import json
from importlib.resources import files

from libris.modules.bibliographic.domain.profile_contract import ProfileDefinition
from libris.modules.bibliographic.domain.profile_registry import (
    ProfileError,
    ProfileRegistry,
    SemanticRegistry,
    ShapeRegistry,
    profile_fingerprint,
)
from libris.modules.bibliographic.domain.profiles import CatalogProfile

LEGACY_PROFILES = {
    "urn:libris:profile:monograph:v1": "monograph-v1.json",
    "urn:libris:profile:monograph:v1:1": "monograph-v1.1.json",
    "urn:libris:profile:authority:v1": "authority-v1.json",
}


def _read(name: str) -> str:
    return files("libris.modules.bibliographic").joinpath("resources", name).read_text("utf-8")


def load_legacy_profile(release_id: str) -> CatalogProfile:
    """v1 view fills absent descriptor metadata only, without claiming extra SHACL rules."""
    try:
        name = LEGACY_PROFILES[release_id]
    except KeyError as error:
        raise ValueError("Perfil legado local desconhecido.") from error
    if name != "monograph-v1.json":
        return CatalogProfile.model_validate_json(_read(name))
    data = json.loads(_read(name))
    data.update(release="1.0", status="candidate")
    for resource in data["resources"]:
        resource["label"] = {"pt": resource["class"].rsplit("/", 1)[-1]}
        for field in resource["fields"]:
            field["name"] = field["property"].rsplit("/", 1)[-1].rsplit("#", 1)[-1]
            field["nodeKind"] = (
                "Literal"
                if field["valueKind"] == "literal"
                else (
                    "BlankNodeOrIRI"
                    if field.get("targetClasses")
                    and not field["property"].endswith(
                        ("instanceOf", "itemOf", "hasInstance", "hasItem")
                    )
                    else "IRI"
                )
            )
            field["minCount"] = int(field["requiredInForm"])
            field["maxCount"] = None if field["repeatable"] else 1
            field["absent"] = "violation" if field["requiredInForm"] else "omit"
            if field.get("datatypes") is True:
                field["datatypes"] = [
                    "http://www.w3.org/2001/XMLSchema#string",
                    "http://www.w3.org/2001/XMLSchema#gYear",
                    "http://www.w3.org/2001/XMLSchema#date",
                ]
            field["validation"] = "Descritor legado; consultar shapes originais para regras RDF."
    return CatalogProfile.model_validate(data)


def load_profile_registry() -> ProfileRegistry:
    """Manifest entries are authored/trusted package data, never user configuration."""
    manifest: list[str] = json.loads(_read("profiles-v2/manifest.json"))
    definitions = [
        ProfileDefinition.model_validate_json(_read(f"profiles-v2/{name}")) for name in manifest
    ]
    fingerprints: dict[str, str] = json.loads(_read("profiles-v2/release-lock.json"))
    if not fingerprints.keys() <= {definition.release_id for definition in definitions}:
        raise ProfileError("missing_release", "Release fixada foi removida do manifest.")
    for definition in definitions:
        expected = fingerprints.get(definition.release_id)
        if (expected is None and definition.status != "draft") or (
            expected is not None and expected != profile_fingerprint(definition)
        ):
            raise ProfileError("immutable_release", "Fingerprint de release ausente ou divergente.")
    registry = ProfileRegistry(
        definitions,
        SemanticRegistry.model_validate_json(_read("profiles-v2/semantics-v1.json")),
        ShapeRegistry.model_validate_json(_read("profiles-v2/shapes-v1.json")),
        used_releases=fingerprints,
    )
    for release_id in fingerprints:
        if not set(registry.resolve(release_id).lineage) <= fingerprints.keys():
            raise ProfileError("unlocked_dependency", "Base de release fixada exige fingerprint.")
    return registry
