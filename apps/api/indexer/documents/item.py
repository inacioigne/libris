from uuid import UUID

from pydantic import BaseModel


class ItemSearchDocument(BaseModel):
    id: UUID
    instance_id: UUID

    uri: str | None = None
    barcode: str | None = None
    location: str | None = None
    call_number: str | None = None
    status: str | None = None