from fastapi.params import Depends
from typing_extensions import Annotated

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.crud.user import get_user_by_id
from core.security import verify_password, decode_access_token
from models.user import User
from core.security import oauth2_scheme
from core.db import get_db


async def authenticate_user(
    db: AsyncSession,
    username: str,
    password: str,
) -> User | None:

    result = await db.execute(
        select(User).where(User.username == username)
    )

    user = result.scalar_one_or_none()

    if not user:
        return None

    if not verify_password(
        password,
        user.password_hash,
    ):
        return None

    return user

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
):
    payload = decode_access_token(token)

    # buscar usuário pelo sub do JWT
    user_id = payload.get("sub")

    user = await get_user_by_id(db, user_id)

    return user