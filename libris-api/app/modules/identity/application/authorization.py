"""Server-owned execution contexts and an injectable, transport-independent guard.

These Python objects are not cryptographic credentials. Only OIDC adapters and
trusted composition roots may construct them; never deserialize request fields.
"""

import re
from dataclasses import dataclass
from uuid import UUID

from app.modules.identity.domain.authorization import (
    POLICIES,
    Operation,
    ResourceContext,
    ResourceKind,
)
from app.modules.identity.domain.exceptions import PermissionDenied
from app.modules.identity.domain.models import AuthenticatedActor, actor_identifier
from app.modules.identity.domain.permissions import Permission
from app.modules.security.application.emission import (
    SecuritySink,
    correlation_id,
    emit_safely,
)
from app.modules.security.domain.events import (
    Action,
    ActorType,
    EventType,
    Outcome,
    Reason,
    SecurityEvent,
)
from app.modules.security.infrastructure.logging import LoggingSecuritySink


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
    def __init__(self, observer: SecuritySink | None = None) -> None:
        self.observer = observer if observer is not None else LoggingSecuritySink()

    def require(
        self,
        *,
        context: ExecutionContext | None,
        operation: Operation,
        resource: ResourceContext,
    ) -> None:
        try:
            self._require(context=context, operation=operation, resource=resource)
        except PermissionDenied as error:
            reasons = {
                "Operação/recurso não autorizado.": Reason.INVALID_OPERATION_RESOURCE,
                "Projeção não publicada.": Reason.UNPUBLISHED_PROJECTION,
                "Operação fora do escopo técnico.": Reason.TECHNICAL_SCOPE,
                "Contexto confiável obrigatório.": Reason.MISSING_CONTEXT,
                "Permissões insuficientes.": Reason.INSUFFICIENT_PERMISSIONS,
            }
            self._observe(
                context, operation, resource, reasons.get(str(error), Reason.INVALID_CONTEXT)
            )
            raise
        self._observe(context, operation, resource, Reason.NONE)

    def _observe(
        self,
        context: ExecutionContext | None,
        operation: Operation,
        resource: ResourceContext,
        reason: Reason,
    ) -> None:
        actor_id = None
        actor_type = ActorType.UNKNOWN
        if isinstance(context, (HumanContext, TechnicalContext)):
            try:
                context.__post_init__()
            except PermissionDenied:
                pass
            else:
                if isinstance(context, HumanContext):
                    actor_id, actor_type = context.actor.actor_id, ActorType.HUMAN
                else:
                    actor_id, actor_type = context.actor_id, ActorType.TECHNICAL
        granted = reason == Reason.NONE
        emit_safely(
            self.observer,
            SecurityEvent(
                event_type=(
                    EventType.AUTHORIZATION_GRANTED if granted else EventType.AUTHORIZATION_DENIED
                ),
                correlation_id=correlation_id(),
                actor_id=actor_id,
                actor_type=actor_type,
                action=operation if isinstance(operation, Operation) else Action.UNKNOWN_OPERATION,
                outcome=Outcome.SUCCESS if granted else Outcome.DENIED,
                reason=reason,
                resource_type=(
                    resource.kind
                    if isinstance(resource, ResourceContext)
                    and isinstance(resource.kind, ResourceKind)
                    else None
                ),
                resource_id=(
                    resource.resource_id
                    if isinstance(resource, ResourceContext)
                    and isinstance(resource.resource_id, UUID)
                    else None
                ),
                component="authorization",
            ),
        )

    def _require(
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
