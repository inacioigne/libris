from aiomysql import IntegrityError
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
from models.instance import Instance
from schemas.instances import InstanceCreate
from sqlalchemy.orm import selectinload

async def create_instance(db: AsyncSession, instance_in: InstanceCreate) -> Instance:
    
    instance = Instance(**instance_in.model_dump())
    db.add(instance)
    await db.commit()
    await db.refresh(instance)
    return instance



async def set_publisher(db: AsyncSession, instance_id: uuid.UUID, agent_id: uuid.UUID | None) -> Instance:
    instance = await db.get(Instance, instance_id)
    if instance is None:
        raise HTTPException(status_code=404, detail="Instance não encontrada")

    instance.publisher_id = agent_id
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=400, detail="agent_id inválido")
    await db.refresh(instance)
    return instance


async def list_instances(db: AsyncSession, offset: int = 0, limit: int = 20):
    result = await db.execute(
        select(Instance)
        .options(selectinload(Instance.publisher))
        .offset(offset)
        .limit(limit)
    )
    
    return result.scalars().all()