from uuid import UUID

# from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.orm import selectinload

from services.repositories.work_repository import WorkRepository
# from models.work import Work
from indexer.elastic.client import get_elasticsearch
from indexer.mappers.work import WorkMapper

INDEX_NAME = "works"


class WorkIndex:

    def __init__(self):
        self.client = get_elasticsearch()

    async def _index(self, work_id: UUID, document: dict):
        await self.client.index(
            index=INDEX_NAME,
            id=str(work_id),
            document=document,
        )

    async def delete(self, work_id: UUID):
        await self.client.delete(
            index=INDEX_NAME,
            id=str(work_id),
            ignore=[404],
        )

    async def get(self, work_id: UUID):
        return await self.client.get(
            index=INDEX_NAME,
            id=str(work_id),
        )

    async def reindex(self, db: AsyncSession, work_id: UUID):

        work = await WorkRepository.get_complete(
            db,
            work_id,
        )

        if work is None:
            return

        document = WorkMapper.from_work(work)

        await self._index(
            work.id,
            document.model_dump(mode="json"),
        )