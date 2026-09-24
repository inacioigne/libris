from fastapi.params import Depends
from fastapi import HTTPException, status
import jwt
from typing_extensions import Annotated

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.crud.user import get_user_by_id
from core.security import get_token_from_cookie, verify_password, decode_access_token
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
    token: Annotated[str, Depends(get_token_from_cookie)],
    db: AsyncSession = Depends(get_db),
):
    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token expirado",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Token inválido",
        )
    
    user_id = payload.get("sub")
    
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Token inválido",
        )

    user = await get_user_by_id(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Usuário não encontrado",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Usuário inativo",
        )

    return user


def require_role(required_role: str):
    async def role_checker(
        current_user: User = Depends(get_current_user),
    ):
        user_roles = {role.name for role in current_user.roles}

        if required_role not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return current_user

    return role_checker
