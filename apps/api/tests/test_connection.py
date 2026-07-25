import pytest
from sqlalchemy import text

from core.db import engine


@pytest.mark.asyncio
async def test_database_connection():
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT 1"))
        assert result.scalar_one() == 1