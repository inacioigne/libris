from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db
from models.instance import Instance
from schemas.instances import InstanceCreate, InstanceRead

router = APIRouter(prefix="/instances", tags=["Instances"])

@router.post("/", response_model=InstanceRead, status_code=201)
async def create_instance(data: InstanceCreate, db: AsyncSession = Depends(get_db)):
    instance = Instance(**data.model_dump())
    db.add(instance)
    await db.commit()
    await db.refresh(instance)
    return instance