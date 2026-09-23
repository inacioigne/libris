from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.work_metadata.workAgent import WorkAgent
from models.work_metadata.workSubject import WorkSubject
from models.work_metadata.work import Work
from models.instance_metadata.instance import Instance


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
    async def has_instances(
        db: AsyncSession,
        work_id,
    ) -> bool:

        result = await db.scalar(
            select(Instance.id)
            .where(Instance.work_id == work_id)
            .limit(1)
        )

        return result is not None
    
    @staticmethod
    async def delete(
        db: AsyncSession,
        work: Work,
    ) -> None:

        await db.delete(work)
        await db.commit()

    @staticmethod
    async def get_complete(
        db: AsyncSession,
        work_id: UUID,
    ) -> Work | None:

        result = await db.execute(
            select(Work)
            .where(Work.id == work_id)
            .options(
            # Agents
            selectinload(Work.agents)
                .selectinload(WorkAgent.agent),

            # Subjects
            selectinload(Work.subjects)
                .selectinload(WorkSubject.subject),

            # Instances
            selectinload(Work.instances)
                .selectinload(Instance.items),

            # Languages
            selectinload(Work.languages),

            # Identifiers
            selectinload(Work.identifiers),

            # Genres
            selectinload(Work.genres),

            # Titles
            selectinload(Work.titles),

            # Notes
            selectinload(Work.notes),

            # Relations
            # selectinload(Work.relations),

            # Types
            selectinload(Work.types),
        )
        )

        return result.scalar_one_or_none()