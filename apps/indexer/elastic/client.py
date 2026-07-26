from functools import lru_cache

from elasticsearch import AsyncElasticsearch

from config import settings


@lru_cache
def get_elasticsearch() -> AsyncElasticsearch:
    return AsyncElasticsearch(
        hosts=[settings.elasticsearch_url],
        request_timeout=30,
        retry_on_timeout=True,
        max_retries=3,
    )


async def close_elasticsearch() -> None:
    client = get_elasticsearch()
    await client.close()