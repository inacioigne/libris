from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.models.instance_metadata.instance import Instance

class InstanceRepository:

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        instance_id: UUID,
    ) -> Instance | None:

        result = await db.execute(
            select(Instance)
            .where(Instance.id == instance_id)
        )

        return result.scalar_one_or_none()