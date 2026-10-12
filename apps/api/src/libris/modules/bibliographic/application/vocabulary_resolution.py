"""Provider boundary and separate enrichment; never overwrite cataloged values."""

from datetime import datetime
from typing import Annotated, Literal, Protocol

from pydantic import AwareDatetime, Field, model_validator

from libris.modules.bibliographic.api.schemas.common import IRI, Contract
from libris.modules.bibliographic.application.controlled_values import (
    ControlledConcept,
    LocalConcept,
)


class ResolutionProvenance(Contract):
    provider: IRI
    source: IRI
    retrieved_at: AwareDatetime
    source_version: str | None = None


class ResolutionSuccess(Contract):
    outcome: Literal["success"]
    uri: IRI
    provenance: ResolutionProvenance
    concept: ControlledConcept

    @model_validator(mode="after")
    def consistent(self) -> "ResolutionSuccess":
        if self.concept.uri != self.uri or self.concept.source != self.provenance.source:
            raise ValueError("Identidade/fonte da resolução diverge da evidência.")
        if self.concept.status not in {"resolved", "deprecated", "invalid"}:
            raise ValueError("Resposta definitiva exige estado conhecido.")
        return self


class ResolutionFailure(Contract):
    outcome: Literal["temporary_failure", "permanent_failure"]
    uri: IRI
    provenance: ResolutionProvenance
    reason: Literal["unavailable", "not_found", "unsupported", "access_denied"]
    retry_after_seconds: int | None = Field(default=None, ge=0, strict=True)

    @model_validator(mode="after")
    def consistent(self) -> "ResolutionFailure":
        if self.outcome == "temporary_failure" and self.reason != "unavailable":
            raise ValueError("Falha transitória exige unavailable.")
        if self.outcome == "permanent_failure" and (
            self.reason == "unavailable" or self.retry_after_seconds is not None
        ):
            raise ValueError("Falha permanente não admite indisponibilidade/retry.")
        return self


ResolutionResult = Annotated[ResolutionSuccess | ResolutionFailure, Field(discriminator="outcome")]


class VocabularyProvider(Protocol):
    async def resolve(self, uri: str) -> ResolutionResult:
        """Resolve exact URI; adapters translate transport errors into typed outcomes."""
        ...


class EnrichedConcept(Contract):
    cataloged: ControlledConcept | LocalConcept
    attempt: ResolutionResult
    previous_success: ResolutionSuccess | None = None

    @model_validator(mode="after")
    def same_identity(self) -> "EnrichedConcept":
        if self.attempt.uri != self.cataloged.uri or (
            self.previous_success is not None and self.previous_success.uri != self.cataloged.uri
        ):
            raise ValueError("Enriquecimento não substitui a identidade catalogada.")
        return self


async def resolve_concept(
    cataloged: ControlledConcept | LocalConcept,
    provider: VocabularyProvider,
    *,
    previous_success: ResolutionSuccess | None = None,
) -> EnrichedConcept:
    """Explicit I/O by application call only; preserve original and last known evidence."""
    original = type(cataloged).model_validate_json(cataloged.model_dump_json())
    result = await provider.resolve(original.uri)
    return EnrichedConcept.model_validate(
        {
            "cataloged": original,
            "attempt": result.model_dump(),
            "previous_success": previous_success.model_dump()
            if previous_success is not None
            else None,
        }
    )


class ResolutionCachePolicy(Contract):
    """Defaults for future bounded caches, not an implemented store."""

    success_ttl_seconds: int = Field(default=86400, ge=0, strict=True)
    negative_ttl_seconds: int = Field(default=300, ge=0, strict=True)
    temporary_retry_seconds: int = Field(default=60, ge=0, strict=True)
    stale_if_unavailable_seconds: int = Field(default=604800, ge=0, strict=True)
    label_update: Literal["explicit_revision"] = "explicit_revision"

    def ttl(self, result: ResolutionResult) -> int:
        if isinstance(result, ResolutionSuccess):
            return self.success_ttl_seconds
        if result.outcome == "permanent_failure":
            return self.negative_ttl_seconds
        return (
            result.retry_after_seconds
            if result.retry_after_seconds is not None
            else self.temporary_retry_seconds
        )

    def fresh(self, result: ResolutionResult, *, now: datetime) -> bool:
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("Instante de consulta exige timezone.")
        age = (now - result.provenance.retrieved_at).total_seconds()
        return 0 <= age < self.ttl(result)

    def usable_stale(
        self, previous: ResolutionSuccess, failure: ResolutionFailure, *, now: datetime
    ) -> bool:
        """Allow last evidence during outage only; this never extends record validity."""
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("Instante de consulta exige timezone.")
        age = (now - previous.provenance.retrieved_at).total_seconds()
        return (
            previous.uri == failure.uri
            and previous.provenance.provider == failure.provenance.provider
            and failure.outcome == "temporary_failure"
            and 0 <= age < self.success_ttl_seconds + self.stale_if_unavailable_seconds
        )
