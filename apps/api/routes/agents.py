from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from services.crud.agent import existing_agent, list_agents
from core.db import get_db
from models.agent import Agent
from schemas.agent import AgentCreate, AgentRead

router = APIRouter(prefix="/agents", tags=["Agents"])

@router.post("/", response_model=AgentRead, status_code=status.HTTP_201_CREATED)
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

@router.get("/", response_model=List[AgentRead], status_code=status.HTTP_200_OK)
async def list_all(
    offset: int = Query(0, ge=0, description="Quantos registros pular"),
    limit: int = Query(20, ge=1, le=100, description="Quantidade máxima de registros"),
    db: AsyncSession = Depends(get_db),
):
    return await list_agents(db, offset=offset, limit=limit)