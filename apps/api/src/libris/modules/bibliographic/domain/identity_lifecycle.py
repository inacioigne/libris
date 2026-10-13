"""Identity retirement contracts; original pairs remain permanently reserved."""

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum

from .errors import CatalogCode, CatalogError
from .models import ResourceIdentity


class IdentityStatus(StrEnum):
    ACTIVE = "active"
    DISCONTINUED = "discontinued"
    REPLACED = "replaced"
    MERGED = "merged"


def invalid(message: str) -> CatalogError:
    return CatalogError(CatalogCode.IDENTITY_OPERATION_INVALID, message)


@dataclass(frozen=True)
class IdentityDecision:
    identity: ResourceIdentity
    status: IdentityStatus
    successor: ResourceIdentity | None
    actor_id: str
    occurred_at: datetime
    justification: str
    evidence: str | None

    def __post_init__(self) -> None:
        if not isinstance(self.status, IdentityStatus) or self.status == IdentityStatus.ACTIVE:
            raise invalid("Decisão deve encerrar uma identidade ativa.")
        if (
            not self.actor_id.strip()
            or not self.justification.strip()
            or (self.occurred_at.tzinfo is None or self.occurred_at.utcoffset() is None)
        ):
            raise invalid("Decisão exige ator, instante com timezone e justificativa.")
        if self.status in {IdentityStatus.REPLACED, IdentityStatus.MERGED}:
            if self.successor is None or (
                self.successor.internal_id == self.identity.internal_id
                or self.successor.uri == self.identity.uri
            ):
                raise invalid("Sucessor/sobrevivente distinto obrigatório.")
        elif self.successor is not None:
            raise invalid("Descontinuação não declara sucessor.")
        if self.status == IdentityStatus.MERGED and (
            self.evidence is None or not self.evidence.strip()
        ):
            raise invalid("Fusão exige evidência explícita.")


@dataclass(frozen=True)
class IdentityLifecycle:
    identity: ResourceIdentity
    status: IdentityStatus = IdentityStatus.ACTIVE
    history: tuple[IdentityDecision, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.status, IdentityStatus):
            raise invalid("Situação de identidade desconhecida.")
        if self.status == IdentityStatus.ACTIVE:
            if self.history:
                raise invalid("Identidade encerrada não pode voltar a ativa.")
        elif len(self.history) != 1 or (
            self.history[-1].identity != self.identity or self.history[-1].status != self.status
        ):
            raise invalid("Encerramento exige decisão histórica correspondente.")

    @property
    def reserved_identity(self) -> ResourceIdentity:
        return self.identity

    def retire(self, decision: IdentityDecision) -> "IdentityLifecycle":
        if self.status != IdentityStatus.ACTIVE or decision.identity != self.identity:
            raise invalid("Operação exige a identidade original ativa.")
        return replace(self, status=decision.status, history=(*self.history, decision))
