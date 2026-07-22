from sqlalchemy.ext.asyncio import AsyncSession

from models.work import Work
from schemas.work import WorkCreate


async def create_work(db: AsyncSession, work_in: WorkCreate) -> Work:
    work = Work(**work_in.model_dump())
    db.add(work)
    await db.commit()
    await db.refresh(work)
    return work