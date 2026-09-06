from pydantic import BaseModel

class WorkTitleSearch(BaseModel):
    value: str
    language: str | None = None
    title_type: str
    is_preferred: bool = False