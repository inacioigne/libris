"""Generate/check v2 schemas and resolved example payloads from Pydantic/package JSON."""

import argparse
import json
from importlib.resources import files
from pathlib import Path

from libris.modules.bibliographic.domain.profile_contract import (
    ProfileDefinition,
    ResolvedProfile,
)
from libris.modules.bibliographic.domain.profile_registry import (
    ProfileRegistry,
    SemanticRegistry,
    ShapeRegistry,
    profile_fingerprint,
)
from libris.modules.bibliographic.infrastructure.profiles import (
    ProfileSemanticRelease,
    load_profile_registry,
    load_semantic_registry,
)

ROOT = Path(__file__).resolve().parents[1]
RESOURCES = ROOT / "apps/api/src/libris/modules/bibliographic/resources/profiles-v2"
EXAMPLES = ROOT / "docs/examples/profiles"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--lock-new-releases",
        action="store_true",
        help="Acrescenta fingerprints de candidatas novas; não sobrescreve releases.",
    )
    args = parser.parse_args()
    artifacts: dict[Path, object] = {
        RESOURCES / "profile-2.0.schema.json": ProfileDefinition.model_json_schema(),
        RESOURCES / "resolved-profile-2.0.schema.json": ResolvedProfile.model_json_schema(),
        RESOURCES / "semantics-1.1.schema.json": SemanticRegistry.model_json_schema(),
        RESOURCES / "shapes-1.0.schema.json": ShapeRegistry.model_json_schema(),
    }
    manifest: list[str] = json.loads(
        files("libris.modules.bibliographic")
        .joinpath("resources/profiles-v2/manifest.json")
        .read_text("utf-8")
    )
    if args.check and args.lock_new_releases:
        parser.error("--check não pode modificar fingerprints.")
    if args.lock_new_releases:
        declarations = [
            ProfileDefinition.model_validate_json((RESOURCES / name).read_text("utf-8"))
            for name in manifest
        ]
        associations = [
            ProfileSemanticRelease.model_validate(entry)
            for entry in json.loads((RESOURCES / "semantic-profile-releases.json").read_text())
        ]
        semantics_by_release: dict[str, SemanticRegistry] = {}
        for association in associations:
            declaration = ProfileDefinition.model_validate_json(
                (RESOURCES / association.profile_file).read_text("utf-8")
            )
            if declaration.release_id != association.profile_release:
                raise SystemExit("Associação semântica aponta a outra release.")
            declarations.append(declaration)
            semantic_registry = load_semantic_registry(association.semantic_release)
            semantic_registry.check_extension_of(load_semantic_registry("1.0"))
            semantics_by_release[declaration.release_id] = semantic_registry
        # Validate complete input before making the artifact concrete.
        candidate_registry = ProfileRegistry(
            declarations,
            SemanticRegistry.model_validate_json(
                (RESOURCES / "semantics-v1.json").read_text("utf-8")
            ),
            ShapeRegistry.model_validate_json((RESOURCES / "shapes-v1.json").read_text("utf-8")),
            semantics_by_release=semantics_by_release,
        )
        lock_path = RESOURCES / "release-lock.json"
        locks: dict[str, str] = json.loads(lock_path.read_text("utf-8"))
        protected = set(locks)
        for declaration in declarations:
            if declaration.status != "draft":
                protected.update(candidate_registry.resolve(declaration.release_id).lineage)
        for declaration in declarations:
            fingerprint = profile_fingerprint(declaration)
            if declaration.release_id in locks and locks[declaration.release_id] != fingerprint:
                raise SystemExit("Release imutável modificada: " + declaration.release_id)
            if declaration.release_id in protected:
                locks[declaration.release_id] = fingerprint
        lock_path.write_text(json.dumps(locks, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    registry = load_profile_registry()
    for name in manifest:
        if name not in {
            "core-2.0.0.json",
            "work-minimal-2.0.0.json",
            "monograph-2.0.0.json",
            "serial-2.0.0.json",
            "digital-2.0.0.json",
        }:
            continue
        definition = ProfileDefinition.model_validate_json((RESOURCES / name).read_text("utf-8"))
        artifacts[EXAMPLES / name] = definition.model_dump(mode="json")
        if name != "monograph-2.0.0.json":
            continue
        artifacts[EXAMPLES / name.replace(".json", ".resolved.json")] = registry.resolve(
            definition.release_id
        ).model_dump(mode="json")
    mismatches: list[str] = []
    for path, value in artifacts.items():
        content = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
        if args.check:
            if not path.exists() or path.read_text("utf-8") != content:
                mismatches.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    if mismatches:
        raise SystemExit("Artefatos divergentes: " + ", ".join(mismatches))
    print(f"{len(artifacts)} artefatos {'verificados' if args.check else 'gerados'}.")


if __name__ == "__main__":
    main()
