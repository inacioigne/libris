from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db
from models.subject import Subject
from schemas.subject import SubjectCreate, SubjectRead
from services.crud.subject import create_subject, existing_subject

router = APIRouter(prefix="/subjects", tags=["Subjects"])


@router.post("/", response_model=SubjectRead, status_code=status.HTTP_201_CREATED)
async def create(
    data: SubjectCreate,
    db: AsyncSession = Depends(get_db),
):
    return await create_subject(db, data)