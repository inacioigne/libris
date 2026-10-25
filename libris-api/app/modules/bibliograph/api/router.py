import json
from importlib.resources import files
from uuid import UUID

from fastapi import APIRouter, Header, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from app.modules.bibliograph.domain.models import BibliographicDraft


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class DraftCreate(ApiModel):
    pass


class DraftRead(ApiModel):
    id: UUID
    catalogerId: UUID


router = APIRouter(prefix="/api/v1/bibliographic", tags=["bibliographic"])


@router.get(
    "/profile/work-default.v1.json",
    operation_id="getDefaultWorkSchema",
    response_class=JSONResponse,
)
async def get_default_work_schema() -> JSONResponse:
    """Return the provisional default Work cataloging schema for the frontend."""
    schema_path = files("app.modules.bibliograph.api.schemas").joinpath(
        "work-default.v1.json"
    )
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    return JSONResponse(content=schema)


@router.post(
    "/drafts",
    operation_id="createBibliographicDraft",
    response_model=DraftRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_draft(
    response: Response,
    payload: DraftCreate | None = None,
    cataloger_id: UUID = Header(alias="X-Cataloger-Id"),
) -> DraftRead:
    """Create the identity of a draft owned by the current cataloger."""
    del payload
    draft = BibliographicDraft.create(cataloger_id)
    response.headers["Location"] = f"/api/v1/bibliographic/drafts/{draft.id}"
    return DraftRead(id=draft.id, catalogerId=draft.cataloger_id)
