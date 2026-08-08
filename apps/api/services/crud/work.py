from sqlalchemy import select
from sqlalchemy.orm import selectinload

from sqlalchemy.ext.asyncio import AsyncSession
from services.indexing.work import WorkIndex
from models.work import Work
from schemas.work import WorkCreate


async def create_work(db: AsyncSession, work_in: WorkCreate) -> Work:
    work = Work(**work_in.model_dump())
    db.add(work)
    await db.commit()
    await db.refresh(work)
    
    await WorkIndex().reindex(db, work.id)
    return work


async def list_works(db: AsyncSession, offset: int = 0, limit: int = 20):
    result = await db.execute(
        select(Work).options(selectinload(Work.agents)).offset(offset).limit(limit)
    )
    return result.scalars().all()