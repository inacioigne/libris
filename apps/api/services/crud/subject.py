import uuid

from aiomysql import IntegrityError
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.associations import WorkSubject
from schemas.subject import SubjectCreate, WorkSubjectCreate, WorkSubjectRead
from models.subject import Subject


async def existing_subject(
    db: AsyncSession,
    preferred_label: str,
) -> Subject | None:
    result = await db.execute(
        select(Subject).where(
            func.lower(Subject.preferred_label)
            == preferred_label.lower()
        )
    )
    return result.scalar_one_or_none()


async def create_subject(
    db: AsyncSession,
    data: SubjectCreate,
) -> Subject:
    existing = await existing_subject(db, data.preferred_label)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe um assunto com este nome."
        )

    subject = Subject(
        preferred_label=data.preferred_label,
    )

    db.add(subject)
    await db.commit()
    await db.refresh(subject)

    return subject

async def list_subjects(db: AsyncSession, offset: int = 0, limit: int = 20):
    result = await db.execute(
        select(Subject).offset(offset).limit(limit)
    )
    return result.scalars().all()

async def link_subject_to_work(work_id: uuid.UUID,
    data: WorkSubjectCreate,
    db: AsyncSession):
    link = WorkSubject(
            work_id=work_id,
            subject_id=data.subject_id,
        )
    
    db.add(link)
    
    try:
        await db.commit()
    
    except IntegrityError as exc:
        await db.rollback()
    
        detail = (
                "já existe uma associação para este trabalho e assunto. "
                f"Detalhes: {exc.orig.args[0] if exc.orig is not None else exc}"
            )
    
        raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=detail,
            )
    
    except Exception as exc:
        await db.rollback()
    
        message = str(exc)
    
        if "duplicate" in message.lower() or "já existe" in message.lower():
            detail = (
                    "já existe uma associação para este trabalho e assunto. "
                    f"Detalhes: {message}"
                )
        else:
                detail = f"Erro ao criar associação: {message}"
    
        raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=detail,
            )
    
    await db.refresh(link)
    
    return link