from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from core.security import create_access_token
from core.db import get_db
from schemas.auth import Token
from services.auth import authenticate_user, get_current_user


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/login",
    # response_model=Token,
)
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    user = await authenticate_user(
        db=db,
        username=form_data.username,
        password=form_data.password,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            # headers={
            #     "WWW-Authenticate": "Bearer",
            # },
        )

    access_token = create_access_token(
        data={
            "sub": str(user.id),
        },
    )
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # True em produção com HTTPS
        samesite="lax",
        max_age=1800,
    )


    # return {
    #     "access_token": access_token,
    #     "token_type": "bearer",
    # }
    return {
        "message": "Login realizado com sucesso"
    }
    
@router.get("/me")
async def me(
    current_user: User = Depends(get_current_user),
):
    return {
        "id": str(current_user.id),
        "username": current_user.username,
        "email": current_user.email,
        "roles": [
            role.name
            for role in current_user.roles
        ],
    }