"""Projeção pública dos perfis locais sem nomes de arquivos de infraestrutura."""

from typing import Literal

from libris.modules.bibliographic.api.schemas.common import Contract
from libris.modules.bibliographic.domain.profile_contract import ResolvedProfile, ShapeReference
from libris.modules.bibliographic.domain.profile_registry import ProfileRegistry
from libris.modules.bibliographic.domain.profiles import ProfileResource
from libris.modules.bibliographic.infrastructure.profiles import (
    LEGACY_PROFILES,
    load_legacy_profile,
    load_profile_registry,
)
from libris.modules.bibliographic.infrastructure.validation import LEGACY_SHAPE_RELEASES


class LegacyProfileRead(Contract):
    format: Literal["libris.legacy-profile"] = "libris.legacy-profile"
    id: str
    release_id: str
    release: str
    status: Literal["candidate"]
    label: dict[str, str]
    resources: list[ProfileResource]
    validation: tuple[ShapeReference, ...]


class ProfileReleaseRead(Contract):
    configured: Literal[True] = True
    # O modelo não registra aprovação institucional; não produzir approved inferido.
    profile: LegacyProfileRead | ResolvedProfile
    persistent_writes_supported: bool


def public_profile(release_id: str, registry: ProfileRegistry | None = None) -> ProfileReleaseRead:
    if release_id in LEGACY_PROFILES:
        legacy = load_legacy_profile(release_id)
        shapes_id, shapes_release = LEGACY_SHAPE_RELEASES[release_id]
        return ProfileReleaseRead(
            profile=LegacyProfileRead(
                id=legacy.id,
                release_id=legacy.id,
                release=legacy.release,
                status=legacy.status,
                label=legacy.label,
                resources=legacy.resources,
                validation=(
                    ShapeReference(id=shapes_id, release=shapes_release, context="snapshot"),
                ),
            ),
            persistent_writes_supported=True,
        )
    return ProfileReleaseRead(
        profile=(registry or load_profile_registry()).resolve(release_id),
        persistent_writes_supported=False,
    )


def public_profiles() -> list[ProfileReleaseRead]:
    registry = load_profile_registry()
    return [
        public_profile(release, registry)
        for release in sorted((*LEGACY_PROFILES, *registry.release_ids()))
    ]
