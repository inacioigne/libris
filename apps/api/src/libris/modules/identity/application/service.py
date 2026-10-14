from collections.abc import Mapping
from typing import Protocol

from libris.modules.identity.domain.exceptions import (
    AuthenticationError,
    PermissionDenied,
    ProviderUnavailable,
)
from libris.modules.identity.domain.models import AuthenticatedActor, actor_identifier
from libris.modules.identity.domain.permissions import Permission
from libris.modules.identity.infrastructure.role_mapper import extract_roles, map_permissions
from libris.modules.security_audit.application.emission import (
    SecuritySink,
    correlation_id,
    emit_safely,
)
from libris.modules.security_audit.domain.events import (
    Action,
    ActorType,
    EventType,
    Outcome,
    Reason,
    SecurityEvent,
)
from libris.modules.security_audit.infrastructure.logging import LoggingSecuritySink


class TokenValidator(Protocol):
    async def validate(self, token: str) -> Mapping[str, object]: ...


class IdentityService:
    def __init__(
        self,
        validator: TokenValidator,
        role_source: str,
        role_client: str,
        human_client: str = "libris-web",
        observer: SecuritySink | None = None,
    ) -> None:
        self.observer = observer if observer is not None else LoggingSecuritySink()
        self.validator = validator
        self.role_source = role_source
        self.role_client = role_client
        if not human_client.strip():
            raise ValueError("Cliente humano OIDC obrigatório.")
        self.human_client = human_client

    def observe_authentication(
        self,
        reason: Reason,
        actor: AuthenticatedActor | None = None,
    ) -> None:
        emit_safely(
            self.observer,
            SecurityEvent(
                event_type=EventType.AUTHENTICATION_SUCCEEDED
                if actor
                else EventType.AUTHENTICATION_FAILED,
                correlation_id=correlation_id(),
                actor_id=actor.actor_id if actor else None,
                actor_type=ActorType.HUMAN if actor else ActorType.UNKNOWN,
                action=Action.AUTHENTICATE,
                component="api",
                reason=reason,
                outcome=Outcome.SUCCESS
                if actor
                else (
                    Outcome.UNAVAILABLE if reason == Reason.PROVIDER_UNAVAILABLE else Outcome.DENIED
                ),
            ),
        )

    async def authenticate(self, token: str) -> AuthenticatedActor:
        try:
            actor = await self._authenticate(token)
        except AuthenticationError as error:
            reason = (
                Reason.PROVIDER_UNAVAILABLE
                if isinstance(error, ProviderUnavailable)
                else Reason(error.reason)
            )
            self.observe_authentication(reason)
            raise
        self.observe_authentication(Reason.NONE, actor)
        return actor

    async def _authenticate(self, token: str) -> AuthenticatedActor:
        claims = await self.validator.validate(token)
        # Only the configured interactive client may enter the human boundary.
        # azp is trusted only after TokenValidator verifies the signed JWT.
        # The provider must disable service accounts/token exchange for this client.
        if claims.get("azp") != self.human_client:
            raise AuthenticationError(reason="client_not_allowed")
        issuer, subject = claims.get("iss"), claims.get("sub")
        if not isinstance(issuer, str) or not isinstance(subject, str) or not subject.strip():
            raise AuthenticationError()
        roles = extract_roles(claims, self.role_source, self.role_client)
        return AuthenticatedActor(
            actor_identifier(issuer, subject), issuer, subject, roles, map_permissions(roles)
        )


def authorize(actor: AuthenticatedActor, permissions: tuple[Permission, ...]) -> None:
    if (
        not isinstance(actor, AuthenticatedActor)
        or any(not isinstance(p, Permission) for p in permissions)
        or not set(permissions).issubset(actor.permissions)
    ):
        raise PermissionDenied()
