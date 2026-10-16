"""Catalog HTTP v1 composition point; domain operations arrive in M05.03–M05.06."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/catalog", tags=["catalog"])
