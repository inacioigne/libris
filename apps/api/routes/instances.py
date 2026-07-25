from typing import List
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db
from models.instance import Instance
from schemas.instances import InstanceCreate, InstanceRead, InstancePublisherUpdate
from services.crud.instance import create_instance, list_instances, set_publisher

router = APIRouter(prefix="/instances", tags=["Instances"])

@router.post("/", response_model=InstanceRead, status_code=201)
async def create(
    data: InstanceCreate,  
    db: AsyncSession = Depends(get_db),
):
    return await create_instance(db, data)


@router.patch("/{instance_id}/publisher", response_model=InstanceRead)
async def update_publisher(
    instance_id: uuid.UUID,
    data: InstancePublisherUpdate,
    db: AsyncSession = Depends(get_db),
):
    return await set_publisher(db, instance_id, data.agent_id)

@router.get("/", response_model=List[InstanceRead], status_code=200)
async def list_all(
    offset: int = Query(0, ge=0, description="Quantos registros pular"),
    limit: int = Query(20, ge=1, le=100, description="Quantidade máxima de registros"),
    db: AsyncSession = Depends(get_db),
):
    return await list_instances(db, offset=offset, limit=limit)