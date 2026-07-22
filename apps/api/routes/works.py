import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models.associations import WorkAgent
from services.crud.work import create_work
from core.db import get_db

from schemas.work import WorkAgentCreate, WorkAgentRead, WorkCreate, WorkRead

router = APIRouter(prefix="/works", tags=["Works"])


@router.post(
    "/", 
    response_model=WorkRead, 
    status_code=status.HTTP_201_CREATED
    )
async def create(
    data: WorkCreate, 
    db: AsyncSession = Depends(get_db)
    ):
    
    return await create_work(db, data)

@router.post("/{work_id}/agents", response_model=WorkAgentRead, status_code=201)
async def link_agent_to_work(
    work_id: uuid.UUID,
    data: WorkAgentCreate,
    db: AsyncSession = Depends(get_db),
):
    link = WorkAgent(work_id=work_id, agent_id=data.agent_id, role=data.role)
    db.add(link)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        detail = (
            f"Associação inválida ou já existente. Detalhes: "
            f"{exc.orig.args[0] if exc.orig is not None else exc}"
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    except Exception as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao criar associação: {exc}"
        )
    await db.refresh(link)
    return link