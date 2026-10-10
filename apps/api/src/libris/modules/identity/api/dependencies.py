from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from libris.modules.identity.application.service import IdentityService, authorize
from libris.modules.identity.domain.exceptions import AuthenticationError, PermissionDenied
from libris.modules.identity.domain.models import AuthenticatedActor
from libris.modules.identity.domain.permissions import Permission

bearer = HTTPBearer(auto_error=False)


def get_identity_service(request: Request) -> IdentityService:
    service: IdentityService = request.app.state.identity_service
    return service


async def get_current_actor(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    service: Annotated[IdentityService, Depends(get_identity_service)],
) -> AuthenticatedActor:
    if credentials is not None:
        try:
            return await service.authenticate(credentials.credentials)
        except AuthenticationError:
            pass
    raise HTTPException(
        status_code=401,
        detail="Autenticação necessária ou inválida.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_permissions(*permissions: Permission) -> Callable[..., AuthenticatedActor]:
    def dependency(
        actor: Annotated[AuthenticatedActor, Depends(get_current_actor)],
    ) -> AuthenticatedActor:
        try:
            authorize(actor, permissions)
        except PermissionDenied as exc:
            raise HTTPException(status_code=403, detail="Permissão insuficiente.") from exc
        return actor

    return dependency
