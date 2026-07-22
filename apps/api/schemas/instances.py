import uuid
from pydantic import BaseModel

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