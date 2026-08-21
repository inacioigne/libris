from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import Role
from schemas.config import settings
from services.crud.user import existing_user, create_user
from schemas.user import UserCreate


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


async def seed_admin_user(db: AsyncSession):
    
    username = settings.admin_username
    password = settings.admin_password
    email = settings.admin_email

    if not username or not password:
        return

    user = await existing_user(db, username=username)
    if user is not None:
        print(f"Admin user '{username}' already exists. Skipping creation.")
        return
    

    # ensure admin role exists
    result = await db.execute(select(Role).where(Role.name == "admin"))
    role = result.scalar_one_or_none()

    if role is None:
        role = Role(name="admin")
        db.add(role)
        await db.commit()
        await db.refresh(role)

    user_in = UserCreate(username=username, email=email or f"{username}@example.com", password=password)
    user = await create_user(user_in, db)
    await db.refresh(user, ["roles"])

    # attach role to user
    user.roles.append(role)
    db.add(user)
    await db.commit()