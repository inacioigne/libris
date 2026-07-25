from sqlalchemy.ext.asyncio import AsyncSession
from models.instance import Instance
from schemas.instances import InstanceCreate

async def create_instance(db: AsyncSession, instance_in: InstanceCreate) -> Instance:
    
    instance = Instance(**instance_in.model_dump())
    db.add(instance)
    await db.commit()
    await db.refresh(instance)
    return instance