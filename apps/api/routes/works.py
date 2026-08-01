from typing import List
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


from schemas.subject import WorkSubjectCreate, WorkSubjectRead
from models.associations import WorkAgent, WorkSubject
from services.crud.work import create_work, list_works
from core.db import get_db

from schemas.work import WorkAgentCreate, WorkAgentRead, WorkCreate, WorkRead
from services.crud.subject import link_subject_to_work

router = APIRouter(prefix="/works", tags=["Works"])


@router.post("/", response_model=WorkRead, status_code=status.HTTP_201_CREATED)
async def create(
    data: WorkCreate, 
    db: AsyncSession = Depends(get_db)
    ):
    
    return await create_work(db, data)

@router.get("/", response_model=List[WorkRead], status_code=status.HTTP_200_OK)
async def list_all(
    offset: int = Query(0, ge=0, description="Quantos registros pular"),
    limit: int = Query(20, ge=1, le=100, description="Quantidade máxima de registros"),
    db: AsyncSession = Depends(get_db),
):
    return await list_works(db, offset=offset, limit=limit)

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
            f"já existe uma associação para este trabalho e agente. "
            f"Detalhes: {exc.orig.args[0] if exc.orig is not None else exc}"
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    except Exception as exc:
        await db.rollback()
        message = str(exc)
        if "duplicate" in message.lower() or "já existe" in message.lower():
            detail = f"já existe uma associação para este trabalho e agente. Detalhes: {message}"
        else:
            detail = f"Erro ao criar associação: {message}"
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    await db.refresh(link)
    return link

@router.post(
    "/{work_id}/subjects",
    response_model=WorkSubjectRead,
    status_code=status.HTTP_201_CREATED,
)
async def subject_to_work(
    work_id: uuid.UUID,
    data: WorkSubjectCreate,
    db: AsyncSession = Depends(get_db),
):
    return await link_subject_to_work(work_id, data, db)