from typing import List
import uuid

from aiomysql import IntegrityError
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.indexing.work import WorkIndex
from indexer.elastic.item import ItemIndex
from indexer.mappers.item import ItemMapper
from models.instance_metadata.instance import Instance
from models.item import Item
from schemas.item import ItemCreate



async def create_items(db: AsyncSession, instance_id: uuid.UUID, data: List[ItemCreate]) -> List[Item]:

    instance = await db.scalar(
        select(Instance).where(Instance.id == instance_id)
    )

    if instance is None:
        raise HTTPException(
            status_code=404,
            detail="Instance não encontrada."
        )

    items = []

    for item_data in data:
        item = Item(
            instance_id=instance_id,
            uri=item_data.uri,
            barcode=item_data.barcode,
            location=item_data.location,
            call_number=item_data.call_number,
            status=item_data.status,
        )

        db.add(item)
        items.append(item)

    await db.commit()

    for item in items:
        await db.refresh(item)
        
     # Indexação no Elasticsearch
    # item_index = ItemIndex()

    # for item in items:
    #     document = ItemMapper.to_search_document(item)

    #     await item_index.index(
    #         item.id,
    #         document.model_dump(mode="json"),
    #     )
    work_index = WorkIndex()
    await work_index.reindex(
        db,
        instance.work_id,
    )

    return items

async def delete_item( db: AsyncSession, item_id: uuid.UUID, ) -> None:
    
    item = await db.scalar(
        select(Item).where(Item.id == item_id)
    )
    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Item não encontrado."
        )
        
    instance = await db.scalar( select(Instance).where(Instance.id == item.instance_id) )
    if instance is None: 
        raise HTTPException( status_code=404, detail="Instance do item não encontrada." )
    
    work_id = instance.work_id

    await db.delete(item)
    await db.commit()

    # # Indexação no Elasticsearch
    # item_index = ItemIndex()
    # await item_index.delete(item_id)
    work_index = WorkIndex()
    await work_index.reindex(db, work_id)


async def list_items(db: AsyncSession, offset: int = 0, limit: int = 20) -> List[Item]:
    result = await db.execute(
        select(Item)
        .offset(offset)
        .limit(limit)
    )
    return result.scalars().all()