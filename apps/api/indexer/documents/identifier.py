from pydantic import BaseModel

class IdentifierSearch(BaseModel):
    type: str
    value: str
    uri: str | None = None
    source: str | None = None