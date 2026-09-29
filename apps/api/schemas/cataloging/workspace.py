from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID


class CatalogingWorkspaceCreate(BaseModel):
    template: str | None = None
    
class CatalogingWorkspaceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_id: UUID

    status: str
    resource_type: str
    template: str | None = None

    data: dict

    created_at: datetime
    updated_at: datetime

    published_at: datetime | None = None
    published_work_id: UUID | None = None