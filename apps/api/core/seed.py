from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import Role


DEFAULT_ROLES = [
    "admin",
    "librarian",
    "user",
]


async def seed_roles(db: AsyncSession):
    for role_name in DEFAULT_ROLES:
        result = await db.execute(
            select(Role).where(Role.name == role_name)
        )

        role = result.scalar_one_or_none()

        if role is None:
            db.add(Role(name=role_name))

    await db.commit()