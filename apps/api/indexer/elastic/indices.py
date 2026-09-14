from indexer.elastic.client import get_elasticsearch

WORKS_INDEX_NAME = "works"
ITEMS_INDEX_NAME = "items"


WORKS_MAPPING = {
    "properties": {
        # vamos definir os campos aqui
    }
}


WORKS_SETTINGS = {
    # analyzers, normalizers etc.
}

ITEMS_SETTINGS = {
    # ...
}


ITEMS_MAPPING = {
    "properties": {
        "id": {
            "type": "keyword"
        },
        "instance_id": {
            "type": "keyword"
        },
        "uri": {
            "type": "keyword"
        },
        "barcode": {
            "type": "keyword"
        },
        "location": {
            "type": "keyword"
        },
        "call_number": {
            "type": "keyword"
        },
        "status": {
            "type": "keyword"
        },
    }
}

async def create_works_index():
    client = get_elasticsearch()

    exists = await client.indices.exists(
        index=WORKS_INDEX_NAME
    )

    if exists:
        return

    await client.indices.create(
        index=WORKS_INDEX_NAME,
        settings=WORKS_SETTINGS,
        mappings=WORKS_MAPPING,
    )
    
async def create_items_index():
    client = get_elasticsearch()

    exists = await client.indices.exists(
        index=ITEMS_INDEX_NAME
    )

    if exists:
        return

    await client.indices.create(
        index=ITEMS_INDEX_NAME,
        settings=ITEMS_SETTINGS,
        mappings=ITEMS_MAPPING,
    )