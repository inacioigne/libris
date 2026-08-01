from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SubjectBase(BaseModel):
    preferred_label: str = Field(..., max_length=255)


class SubjectCreate(SubjectBase):
    pass


class SubjectRead(SubjectBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)
    
class WorkSubjectCreate(BaseModel):
    subject_id: UUID


class WorkSubjectRead(BaseModel):
    work_id: UUID
    subject_id: UUID

    model_config = ConfigDict(from_attributes=True)