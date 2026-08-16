import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.security import hash_password
from models.user import User
from schemas.user import UserCreate



async def create_user(
    data: UserCreate,
    db: AsyncSession,
) -> User:
    user = User(
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password)
    )

    db.add(user)

    await db.commit()
    await db.refresh(user)

    return user



async def existing_user(
    db: AsyncSession,
    username: str | None = None,
    email: str | None = None,
) -> User | None:

    query = select(User)

    if username is not None:
        query = query.where(User.username == username)

    if email is not None:
        query = query.where(User.email == email)

    result = await db.execute(query)

    return result.scalar_one_or_none()

async def get_user_by_id(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> User | None:
    result = await db.execute(
        select(User).where(User.id == user_id)
    )

    return result.scalar_one_or_none()