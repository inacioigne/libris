from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AgentCreate(BaseModel):
    name: str
    type: str | None = None
    identifier: str | None = None


class AgentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    agent_id: UUID
    name: str
    type: str | None
    identifier: str | None