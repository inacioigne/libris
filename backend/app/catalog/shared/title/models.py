from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)

class Title(StrictModel):
    main_title: str = Field(min_length=1)
    subtitle: str | None = None
    part_number: str | None = None
    part_name: str | None = None
    language: str | None = Field(default=None, pattern=r'^[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*$')

    @field_validator('subtitle','part_number','part_name')
    @classmethod
    def nonblank(cls, v):
        if v is not None and not v.strip():
            raise ValueError('must not be blank')
        return v

class VariantTitle(Title):
    type: Literal['variant'] = 'variant'

class ParallelTitle(Title):
    type: Literal['parallel'] = 'parallel'

class TitleSet(StrictModel):
    title: Title
    variant_titles: list[VariantTitle] = Field(default_factory=list)
    parallel_titles: list[ParallelTitle] = Field(default_factory=list)

    @model_validator(mode='after')
    def distinct(self):
        values = [(x.main_title.casefold(),x.subtitle.casefold() if x.subtitle else '',x.part_number or '',x.part_name or '',x.language or '') for x in [self.title,*self.variant_titles,*self.parallel_titles]]
        if len(values) != len(set(values)):
            raise ValueError('duplicate title')
        return self

class WorkTitleRecord(StrictModel):
    kind: Literal['work'] = 'work'
    id: str = Field(pattern=r'^https?://[^\s]+$')
    titles: TitleSet

class InstanceTitleRecord(StrictModel):
    kind: Literal['instance'] = 'instance'
    id: str = Field(pattern=r'^https?://[^\s]+$')
    work_id: str = Field(pattern=r'^https?://[^\s]+$')
    titles: TitleSet

    @model_validator(mode='after')
    def not_self(self):
        if self.id == self.work_id:
            raise ValueError('instance and work must have distinct IRIs')
        return self
