from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from services.cataloging.workspace_service import create_workspace
from services.auth import require_role
from schemas.cataloging.workspace import CatalogingWorkspaceCreate, CatalogingWorkspaceRead
from core.db import get_db

# from app.schemas.cataloging.workspace import (
#     CatalogingWorkspaceCreate,
#     CatalogingWorkspaceRead,
# )
# from app.services.cataloging.workspace_service import create_workspace
# from app.auth.dependencies import get_current_user


router = APIRouter(
    prefix="/cataloging/workspaces",
    tags=["Cataloging"],
)


@router.post(
    "",
    response_model=CatalogingWorkspaceRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_workspace(
    data: CatalogingWorkspaceCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin"))
):
    workspace = await create_workspace(
        db,
        owner_id=current_user.id,
        data=data,
    )

    await db.commit()
    await db.refresh(workspace)

    return workspace