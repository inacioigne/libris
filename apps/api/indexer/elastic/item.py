from uuid import UUID

from indexer.elastic.client import get_elasticsearch


INDEX_NAME = "items"


class ItemIndex:

    def __init__(self):
        self.client = get_elasticsearch()

    async def index(
        self,
        item_id: UUID,
        document: dict,
    ) -> None:
        await self.client.index(
            index=INDEX_NAME,
            id=str(item_id),
            document=document,
        )

    async def delete(
        self,
        item_id: UUID,
    ) -> None:
        await self.client.delete(
            index=INDEX_NAME,
            id=str(item_id),
            ignore=[404],
        )

    async def get(
        self,
        item_id: UUID,
    ):
        return await self.client.get(
            index=INDEX_NAME,
            id=str(item_id),
        )