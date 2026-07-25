from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db
from models.instance import Instance
from schemas.instances import InstanceCreate, InstanceRead
from services.crud.instance import create_instance

router = APIRouter(prefix="/instances", tags=["Instances"])

@router.post("/", response_model=InstanceRead, status_code=201)
async def create(
    data: InstanceCreate,  
    db: AsyncSession = Depends(get_db),
):
    return await create_instance(db, data)