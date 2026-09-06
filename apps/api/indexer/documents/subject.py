from uuid import UUID
from pydantic import BaseModel

class SubjectSearch(BaseModel):
    id: UUID
    label: str
    sequence: int | None = None