# services/cataloging/workspace_service.py

from sqlalchemy.ext.asyncio import AsyncSession

from schemas.cataloging.workspace import CatalogingWorkspaceCreate
from services.repositories.workspace_repository import ( create_workspace as repository_create_workspace)


async def create_workspace(
    db: AsyncSession,
    *,
    owner_id,
    data: CatalogingWorkspaceCreate,
):
    workspace_data = build_initial_data(data.template)

    workspace = await repository_create_workspace(
        db,
        owner_id=owner_id,
        template=data.template,
        data=workspace_data,
    )

    return workspace


def build_initial_data(template: str | None) -> dict:

    if template == "monograph":
        return {
            "work": {
                "types": ["Text"],
                "languages": [],
                "titles": [],
                "agents": [],
                "subjects": [],
            },
            "instances": [
                {
                    "data": {},
                    "items": [],
                }
            ],
        }

    return {
        "work": {},
        "instances": [],
    }