"""Server-owned execution contexts and an injectable, transport-independent guard.

These Python objects are not cryptographic credentials. Only OIDC adapters and
trusted composition roots may construct them; never deserialize request fields.
"""

import re
from dataclasses import dataclass

from libris.modules.identity.domain.authorization import (
    POLICIES,
    Operation,
    ResourceContext,
    ResourceKind,
)
from libris.modules.identity.domain.exceptions import PermissionDenied
from libris.modules.identity.domain.models import AuthenticatedActor, actor_identifier
from libris.modules.identity.domain.permissions import Permission


@dataclass(frozen=True)
class HumanContext:
    actor: AuthenticatedActor

    def __post_init__(self) -> None:
        actor = self.actor
        if (
            not isinstance(actor, AuthenticatedActor)
            or not isinstance(actor.issuer, str)
            or not isinstance(actor.subject, str)
            or not isinstance(actor.permissions, frozenset)
            or not actor.issuer.strip()
            or not actor.subject.strip()
            or actor.actor_id != actor_identifier(actor.issuer, actor.subject)
            or any(not isinstance(p, Permission) for p in actor.permissions)
        ):
            raise PermissionDenied("Contexto humano inválido.")


@dataclass(frozen=True)
class TechnicalContext:
    actor_id: str
    permissions: frozenset[Permission]
    operations: frozenset[Operation]
    origin: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.actor_id, str)
            or not isinstance(self.origin, str)
            or not re.fullmatch(r"(?:service|automated):[a-z][a-z0-9_.-]{0,63}", self.actor_id)
            or not self.origin.strip()
            or not isinstance(self.permissions, frozenset)
            or not isinstance(self.operations, frozenset)
            or any(not isinstance(p, Permission) for p in self.permissions)
            or any(
                not isinstance(op, Operation) or not POLICIES[op].technical
                for op in self.operations
            )
            or Permission.SYSTEM_ADMIN in self.permissions
        ):
            raise PermissionDenied("Contexto técnico inválido.")


ExecutionContext = HumanContext | TechnicalContext


def execution_context(
    context: ExecutionContext | None,
    actor: AuthenticatedActor | None = None,
) -> ExecutionContext | None:
    """Compatibility adapter for trusted M03 callers carrying an OIDC actor."""
    if context is not None and actor is not None:
        raise PermissionDenied("Contextos de execução conflitantes.")
    return HumanContext(actor) if actor is not None else context


class AuthorizationGuard:
    def require(
        self,
        *,
        context: ExecutionContext | None,
        operation: Operation,
        resource: ResourceContext,
    ) -> None:
        policy = POLICIES.get(operation) if isinstance(operation, Operation) else None
        if (
            policy is None
            or not isinstance(resource, ResourceContext)
            or resource.kind not in policy.resources
            or not isinstance(resource.kind, ResourceKind)
            or (not policy.public and not policy.permissions)
        ):
            raise PermissionDenied("Operação/recurso não autorizado.")
        if policy.published_projection:
            if (
                resource.state != "published"
                or type(resource.public_revision) is not int
                or resource.public_revision < 1
                or resource.selected_revision != resource.public_revision
                or type(resource.selected_revision) is not int
            ):
                raise PermissionDenied("Projeção não publicada.")
        if policy.public:
            return
        if isinstance(context, HumanContext):
            context.__post_init__()
            permissions = context.actor.permissions
        elif isinstance(context, TechnicalContext):
            context.__post_init__()
            if not policy.technical or operation not in context.operations:
                raise PermissionDenied("Operação fora do escopo técnico.")
            permissions = context.permissions
        else:
            raise PermissionDenied("Contexto confiável obrigatório.")
        if not policy.permissions.issubset(permissions):
            raise PermissionDenied("Permissões insuficientes.")
