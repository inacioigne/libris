from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.agent import Agent


async def existing_agent(db: AsyncSession, identifier: str) -> bool:
    result = await db.execute(
        select(Agent).where(Agent.identifier == identifier)
    )
    existing = result.scalar_one_or_none()
    return existing
    
    