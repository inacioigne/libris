from indexer.elastic.client import get_elasticsearch

INDEX_NAME = "works"


WORKS_MAPPING = {
    "properties": {
        # vamos definir os campos aqui
    }
}


WORKS_SETTINGS = {
    # analyzers, normalizers etc.
}


async def create_works_index():
    client = get_elasticsearch()

    exists = await client.indices.exists(index=INDEX_NAME)

    if exists:
        return

    await client.indices.create(
        index=INDEX_NAME,
        settings=WORKS_SETTINGS,
        mappings=WORKS_MAPPING,
    )