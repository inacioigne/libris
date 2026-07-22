from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

DATABASE_URL = "mysql+aiomysql://libris_user:8486@localhost:3306/libris_db"

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    pool_pre_ping=True,
)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

class Base(DeclarativeBase):
    pass


async def get_db():
    async with SessionLocal() as session:
        yield session
