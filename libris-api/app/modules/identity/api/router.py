from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.modules.identity.api.dependencies import get_current_actor
from app.modules.identity.domain.models import AuthenticatedActor
from app.modules.identity.domain.permissions import Permission

router = APIRouter(prefix="/api/v1/identity", tags=["identity"])


class IdentityResponse(BaseModel):
    actor_id: str
    display_name: str | None
    picture_url: str | None
    roles: list[str]
    permissions: list[Permission]


@router.get("/me", response_model=IdentityResponse)
async def me(
    actor: Annotated[AuthenticatedActor, Depends(get_current_actor)]
) -> IdentityResponse:
    return IdentityResponse(
        actor_id=actor.actor_id,
        display_name=actor.display_name,
        picture_url=actor.picture_url,
        roles=sorted(actor.roles),
        permissions=sorted(actor.permissions),
    )
