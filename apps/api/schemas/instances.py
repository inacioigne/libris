import uuid
from pydantic import BaseModel, ConfigDict

from schemas.agent import AgentRead

class InstanceCreate(BaseModel):
    work_id: uuid.UUID
    isbn: str | None = None
    publisher_id: uuid.UUID | None = None
    publication_year: int | None = None
    publication_place: str | None = None
    edition: str | None = None
    carrier: str | None = None
    extent: str | None = None
    dimensions: str | None = None

class InstanceRead(BaseModel):
    id: uuid.UUID
    work_id: uuid.UUID
    isbn: str | None = None
    publisher: AgentRead | None = None
    publication_year: int | None = None
    publication_place: str | None = None
    edition: str | None = None
    carrier: str | None = None
    extent: str | None = None
    dimensions: str | None = None
    model_config = ConfigDict(from_attributes=True)
        
class InstancePublisherUpdate(BaseModel):
    agent_id: uuid.UUID | None  