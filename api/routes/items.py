from typing import List
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db
from schemas.item import ItemCreate, ItemRead
from services.crud.item import create_items, list_items

router = APIRouter(prefix="/items", tags=["Items"])


@router.post("/{instance_id}", response_model=List[ItemRead], status_code=201)
async def create(
    instance_id: uuid.UUID,
    data: List[ItemCreate],
    db: AsyncSession = Depends(get_db),
):
    return await create_items(db, instance_id, data)


@router.get("/", response_model=List[ItemRead], status_code=200)
async def list_all(
    offset: int = Query(0, ge=0, description="Quantos registros pular"),
    limit: int = Query(20, ge=1, le=100, description="Quantidade máxima de registros"),
    db: AsyncSession = Depends(get_db),
):
    return await list_items(db, offset=offset, limit=limit)