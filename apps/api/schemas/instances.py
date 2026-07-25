import uuid
from pydantic import BaseModel, ConfigDict

from schemas.agent import AgentRead

class InstanceCreate(BaseModel):
    work_id: uuid.UUID
    isbn: str | None = None
    publisher: str | None = None
    publication_year: int | None = None
    formato: str | None = None

class InstanceRead(InstanceCreate):
    id: uuid.UUID

    class Config:
        from_attributes = True
        
class InstanceRead(BaseModel):
    id: uuid.UUID
    work_id: uuid.UUID
    isbn: str | None = None
    publisher: AgentRead | None = None  
    publication_year: int | None = None
    formato: str | None = None

    model_config = ConfigDict(from_attributes=True)
        
class InstancePublisherUpdate(BaseModel):
    agent_id: uuid.UUID | None  