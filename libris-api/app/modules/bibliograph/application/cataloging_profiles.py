import json
from functools import lru_cache
from importlib.resources import files

from pydantic import BaseModel, ConfigDict


class CatalogingProfileField(BaseModel):
    model_config = ConfigDict(extra="allow", frozen=True)
    id: str
    repeatable: bool = False
    vocabulary: str | None = None
    widget: str


class CatalogingProfileSection(BaseModel):
    model_config = ConfigDict(extra="allow", frozen=True)
    fields: tuple[CatalogingProfileField, ...]


class CatalogingProfile(BaseModel):
    model_config = ConfigDict(extra="allow", frozen=True)
    id: str
    version: str
    sections: tuple[CatalogingProfileSection, ...]


@lru_cache
def get_default_work_profile() -> CatalogingProfile:
    resource = files("app.modules.bibliograph.api.schemas").joinpath(
        "work-default.v1.json"
    )
    return CatalogingProfile.model_validate_json(resource.read_text(encoding="utf-8"))


def get_default_work_profile_document() -> dict[str, object]:
    resource = files("app.modules.bibliograph.api.schemas").joinpath(
        "work-default.v1.json"
    )
    return json.loads(resource.read_text(encoding="utf-8"))
