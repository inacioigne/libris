import uuid
from pydantic import BaseModel, ConfigDict


class WorkBase(BaseModel):
    title: str
    type: str | None = None
    # subject: str | None = None


class WorkCreate(WorkBase):
    pass


class WorkRead(WorkBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    
class WorkAgentCreate(BaseModel):
    agent_id: uuid.UUID
    role: str | None = None

class WorkAgentRead(WorkAgentCreate):
    work_id: uuid.UUID
    class Config:
        from_attributes = True