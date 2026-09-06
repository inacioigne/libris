from uuid import UUID
from pydantic import BaseModel


class AgentSearch(BaseModel):
    id: UUID
    name: str
    role: str
    primary: bool = False
    sequence: int | None = None