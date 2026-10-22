from uuid import UUID

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app.modules.bibliograph.api.schemas import ( WorkCreate )


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Contributor(ApiModel):
    agentId: UUID
    role: str = Field(min_length=1)


class ProfileReference(ApiModel):
    id: str = Field(min_length=1)
    version: str = Field(min_length=1)


# class WorkCreate(ApiModel):
#     title: str = Field(min_length=1)
#     language: str | None = None
#     contributors: list[Contributor] = Field(default_factory=list)
#     subjectIds: list[UUID] = Field(default_factory=list)
#     profile: ProfileReference


class Problem(BaseModel):
    type: str
    title: str
    status: int
    detail: str


router = APIRouter(prefix="/api/v1/bibliographic", tags=["bibliographic works"])


@router.post(
    "/works",
    operation_id="createWork",
    # response_model=WorkRead, 
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    responses={
        status.HTTP_501_NOT_IMPLEMENTED: {
            "model": Problem,
            "description": "Work creation is not implemented yet.",
        }
    },
)
async def create_work(payload: WorkCreate) -> JSONResponse:
    """Expose the provisional Work creation boundary without creating data."""
    # problem = Problem(
    #     type="about:blank",
    #     title="Not Implemented",
    #     status=status.HTTP_501_NOT_IMPLEMENTED,
    #     detail="Work creation is not implemented yet.",
    # )
    # return JSONResponse(
    #     status_code=status.HTTP_501_NOT_IMPLEMENTED,
    #     content=problem.model_dump(),
    #     media_type="application/problem+json",
    # )
    return payload
