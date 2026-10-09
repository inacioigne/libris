from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from libris.core.config import Settings


class Base(DeclarativeBase):
    """Migration metadata; no business tables exist in this stage."""


class Database:
    """Application-scoped async engine and session factory; no implicit commits."""

    def __init__(self, settings: Settings) -> None:
        self.engine = create_async_engine(str(settings.database_url), pool_pre_ping=True)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    async def session(self) -> AsyncIterator[AsyncSession]:
        async with self.sessions() as session:
            yield session

    async def close(self) -> None:
        await self.engine.dispose()
