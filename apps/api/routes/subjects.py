from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db
from models.subject import Subject
from schemas.subject import SubjectCreate, SubjectRead
from services.crud.subject import create_subject, existing_subject, list_subjects

router = APIRouter(prefix="/subjects", tags=["Subjects"])


@router.post("/", response_model=SubjectRead, status_code=status.HTTP_201_CREATED)
async def create(
    data: SubjectCreate,
    db: AsyncSession = Depends(get_db),
):
    return await create_subject(db, data)

@router.get("/", response_model=List[SubjectRead], status_code=status.HTTP_200_OK)
async def list_all(
    offset: int = Query(0, ge=0, description="Quantos registros pular"),
    limit: int = Query(20, ge=1, le=100, description="Quantidade máxima de registros"),
    db: AsyncSession = Depends(get_db),
):
    return await list_subjects(db, offset=offset, limit=limit)