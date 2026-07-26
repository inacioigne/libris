import uuid
 
from pydantic import BaseModel, ConfigDict
 
 
class ItemCreate(BaseModel):
    barcode: str | None = None
    location: str | None = None
    call_number: str | None = None
    status: str | None = None
 
 
class ItemRead(ItemCreate):
    id: uuid.UUID
 
    model_config = ConfigDict(from_attributes=True)