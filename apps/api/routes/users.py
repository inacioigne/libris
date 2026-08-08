import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db
from schemas.user import UserCreate, UserRead
from services.crud.user import create_user


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.post(
    "/",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_user_endpoint(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    user = await create_user(
        db=db,
        data=data,
    )

    return user