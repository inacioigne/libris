from uuid import UUID
from pydantic import BaseModel, ConfigDict
 
 
class ItemCreate(BaseModel): 
    instance_id: UUID
    uri: str | None = None 
    barcode: str | None = None 
    location: str | None = None 
    call_number: str | None = None 
    status: str | None = None
 
 
class ItemRead(ItemCreate):
    id: UUID
 
    model_config = ConfigDict(from_attributes=True)