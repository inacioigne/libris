from uuid import UUID

from pydantic import BaseModel, ConfigDict

from indexer.documents.agent import AgentSearch
from indexer.documents.identifier import IdentifierSearch
from indexer.documents.subject import SubjectSearch
from indexer.documents.workTitle import WorkTitleSearch


class InstanceSummary(BaseModel):
    id: UUID
    isbn: str | None = None
    publication_year: int | None = None
    formato: str | None = None
    publisher_id: UUID | None = None


class WorkSearchDocument(BaseModel):
    id: UUID

    uri: str | None = None

    title: str

    titles: list[WorkTitleSearch] = []

    types: list[str] = []

    languages: list[str] = []

    genres: list[str] = []

    agents: list[AgentSearch] = []

    subjects: list[SubjectSearch] = []

    summary: str | None = None

    notes: list[str] = []

    identifiers: list[IdentifierSearch] = []

    instances: list[InstanceSummary] = []

    instance_count: int = 0

    available_item_count: int = 0