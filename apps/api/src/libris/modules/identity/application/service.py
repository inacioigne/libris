from collections.abc import Mapping
from typing import Protocol

from libris.modules.identity.domain.exceptions import AuthenticationError, PermissionDenied
from libris.modules.identity.domain.models import AuthenticatedActor, actor_identifier
from libris.modules.identity.domain.permissions import Permission
from libris.modules.identity.infrastructure.role_mapper import extract_roles, map_permissions


class TokenValidator(Protocol):
    async def validate(self, token: str) -> Mapping[str, object]: ...


class IdentityService:
    def __init__(self, validator: TokenValidator, role_source: str, role_client: str) -> None:
        self.validator = validator
        self.role_source = role_source
        self.role_client = role_client

    async def authenticate(self, token: str) -> AuthenticatedActor:
        claims = await self.validator.validate(token)
        issuer, subject = claims.get("iss"), claims.get("sub")
        if not isinstance(issuer, str) or not isinstance(subject, str) or not subject.strip():
            raise AuthenticationError()
        roles = extract_roles(claims, self.role_source, self.role_client)
        return AuthenticatedActor(
            actor_identifier(issuer, subject), issuer, subject, roles, map_permissions(roles)
        )


def authorize(actor: AuthenticatedActor, permissions: tuple[Permission, ...]) -> None:
    if not set(permissions).issubset(actor.permissions):
        raise PermissionDenied()
