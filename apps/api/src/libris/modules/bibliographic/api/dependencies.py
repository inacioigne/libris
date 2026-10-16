"""HTTP access to the lifespan-owned factory; application services own transactions.

Identity/context/guard dependencies are reused directly from identity.api.dependencies.
Correlation is supplied by the existing middleware and request_id_context.
"""

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from libris.infrastructure.database import Database


def get_session_factory(request: Request) -> async_sessionmaker[AsyncSession]:
    """Return the existing factory without opening a session or transaction."""
    database: Database = request.app.state.database
    return database.sessions
