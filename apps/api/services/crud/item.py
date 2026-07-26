from typing import List
import uuid

from aiomysql import IntegrityError
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.instance import Instance
from models.item import Item
from schemas.item import ItemCreate



async def create_items(
    db: AsyncSession,
    instance_id: uuid.UUID,
    data: List[ItemCreate],
) -> List[Item]:

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

    return items


async def list_items(db: AsyncSession, offset: int = 0, limit: int = 20) -> List[Item]:
    result = await db.execute(
        select(Item)
        .offset(offset)
        .limit(limit)
    )
    return result.scalars().all()