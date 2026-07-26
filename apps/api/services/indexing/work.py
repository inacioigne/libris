from indexer.elastic.work_index import WorkIndex
from indexer.mappers.work import WorkMapper
from models.work import Work

async def index_work(work: Work):

    document = WorkMapper.from_work(work)

    await WorkIndex().index(
        str(work.id),
        document.model_dump()
    )