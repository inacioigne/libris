from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from libris.modules.identity.application.authorization import AuthorizationGuard, HumanContext
from libris.modules.identity.application.service import IdentityService, authorize
from libris.modules.identity.domain.exceptions import AuthenticationError, PermissionDenied
from libris.modules.identity.domain.models import AuthenticatedActor, actor_identifier
from libris.modules.identity.domain.permissions import Permission
from libris.modules.security_audit.application.emission import correlation_id, emit_safely
from libris.modules.security_audit.domain.events import (
    Action,
    ActorType,
    EventType,
    Outcome,
    Reason,
    SecurityEvent,
)

bearer = HTTPBearer(auto_error=False)


def get_identity_service(request: Request) -> IdentityService:
    service: IdentityService = request.app.state.identity_service
    return service


async def get_current_actor(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    service: Annotated[IdentityService, Depends(get_identity_service)],
    request: Request,
) -> AuthenticatedActor:
    if credentials is not None:
        try:
            return await service.authenticate(credentials.credentials)
        except AuthenticationError:
            pass
    else:
        service.observe_authentication(
            Reason.MALFORMED_BEARER
            if request.headers.get("authorization")
            else Reason.MISSING_BEARER
        )
    raise HTTPException(
        status_code=401,
        detail="Autenticação necessária ou inválida.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_permissions(*permissions: Permission) -> Callable[..., AuthenticatedActor]:
    def dependency(
        actor: Annotated[AuthenticatedActor, Depends(get_current_actor)],
        service: Annotated[IdentityService, Depends(get_identity_service)],
    ) -> AuthenticatedActor:
        allowed = False
        try:
            authorize(actor, permissions)
            allowed = True
        except PermissionDenied as exc:
            raise HTTPException(status_code=403, detail="Permissão insuficiente.") from exc
        finally:
            # Actor normally comes from the OIDC dependency. Overrides remain test-only.
            trusted = actor.actor_id == actor_identifier(actor.issuer, actor.subject)
            emit_safely(
                service.observer,
                SecurityEvent(
                    event_type=EventType.AUTHORIZATION_GRANTED
                    if allowed
                    else EventType.AUTHORIZATION_DENIED,
                    correlation_id=correlation_id(),
                    action=Action.PERMISSION_CHECK,
                    required_permissions=tuple(p for p in permissions if isinstance(p, Permission)),
                    actor_id=actor.actor_id if trusted else None,
                    actor_type=ActorType.HUMAN if trusted else ActorType.UNKNOWN,
                    outcome=Outcome.SUCCESS if allowed else Outcome.DENIED,
                    reason=Reason.NONE if allowed else Reason.INSUFFICIENT_PERMISSIONS,
                    component="api",
                ),
            )
        return actor

    return dependency


async def get_execution_context(
    actor: Annotated[AuthenticatedActor, Depends(get_current_actor)],
) -> HumanContext:
    return HumanContext(actor)


def get_authorization_guard() -> AuthorizationGuard:
    return AuthorizationGuard()
