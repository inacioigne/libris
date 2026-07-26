from indexer.elastic.client import get_elasticsearch

INDEX_NAME = "works"


class WorkIndex:

    def __init__(self):
        self.client = get_elasticsearch()

    async def index(self, work_id: str, document: dict):
        await self.client.index(
            index=INDEX_NAME,
            id=work_id,
            document=document,
        )

    async def delete(self, work_id: str):
        await self.client.delete(
            index=INDEX_NAME,
            id=work_id,
            ignore=[404],
        )

    async def get(self, work_id: str):
        return await self.client.get(
            index=INDEX_NAME,
            id=work_id,
        )