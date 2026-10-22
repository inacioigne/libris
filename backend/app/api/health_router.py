from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok"]


health_router = APIRouter(tags=["health"])


@health_router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Report whether the API process is ready to receive requests."""
    return HealthResponse(status="ok")
