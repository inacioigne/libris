from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from services.crud.agent import existing_agent
from core.db import get_db
from models.agent import Agent
from schemas.agent import AgentCreate, AgentRead

router = APIRouter(prefix="/agents", tags=["Agents"])


@router.post(
    "/",
    response_model=AgentRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_agent(
    data: AgentCreate,
    db: AsyncSession = Depends(get_db),
):
    if data.identifier:
        existing = await existing_agent(db, data.identifier)
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Já existe um agente com este identifier."
            )
            
    agent = Agent(
        name=data.name,
        type=data.type,
        identifier=data.identifier,
    )

    db.add(agent)
    await db.commit()
    await db.refresh(agent)

    return agent