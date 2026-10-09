from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: Literal["libris-api"] = "libris-api"


@router.get("/health", response_model=HealthResponse, summary="Application liveness")
async def health() -> HealthResponse:
    """Report application liveness, without claiming external service readiness."""
    return HealthResponse()
