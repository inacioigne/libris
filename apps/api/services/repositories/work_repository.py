from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.work_metadata.work import Work
from models.instance import Instance


class WorkRepository:

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        work_id: UUID,
    ) -> Work | None:

        result = await db.execute(
            select(Work).where(Work.id == work_id)
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def get_complete(
        db: AsyncSession,
        work_id: UUID,
    ) -> Work | None:

        result = await db.execute(
            select(Work)
            .where(Work.id == work_id)
            .options(
                selectinload(Work.agents),
                selectinload(Work.subjects),
                # selectinload(Work.languages),
                # selectinload(Work.identifiers),
                selectinload(Work.instances)
                    .selectinload(Instance.items),
            )
        )

        return result.scalar_one_or_none()