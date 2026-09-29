from sqlalchemy.ext.asyncio import AsyncSession

from models.cataloging.workspace import CatalogingWorkspace

# from app.models.cataloging.workspace import CatalogingWorkspace


async def create_workspace(
    db: AsyncSession,
    *,
    owner_id,
    template: str | None,
    data: dict,
) -> CatalogingWorkspace:

    workspace = CatalogingWorkspace(
        owner_id=owner_id,
        status="draft",
        resource_type="bibliographic",
        template=template,
        data=data,
    )

    db.add(workspace)

    await db.flush()
    await db.refresh(workspace)

    return workspace