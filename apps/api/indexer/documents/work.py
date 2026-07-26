from uuid import UUID

from pydantic import BaseModel, ConfigDict


class InstanceSummary(BaseModel):
    id: UUID
    edition: str | None = None
    publisher: str | None = None
    publication_date: int | None = None
    isbn: str | None = None


class WorkSearchDocument(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID

    title: str

    subtitle: str | None = None

    authors: list[str] = []

    subjects: list[str] = []

    languages: list[str] = []

    summary: str | None = None

    identifiers: list[str] = []

    instances: list[InstanceSummary] = []

    instance_count: int = 0

    available_item_count: int = 0