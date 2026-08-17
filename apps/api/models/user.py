import uuid

from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base


class User(Base):
    __tablename__ = "user"

    id: Mapped[uuid.UUID] = mapped_column(CHAR(36), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    roles: Mapped[list["Role"]] = relationship(
        secondary="user_role",
        back_populates="users",
    )
    
    
class Role(Base):
    __tablename__ = "role"

    id: Mapped[uuid.UUID] = mapped_column(CHAR(36), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    
    users: Mapped[list["User"]] = relationship(
        secondary="user_role",
        back_populates="roles",
    )
    


class UserRole(Base):
    __tablename__ = "user_role"

    user_id: Mapped[uuid.UUID] = mapped_column(CHAR(36), ForeignKey("user.id", ondelete="CASCADE"), primary_key=True)
    role_id: Mapped[uuid.UUID] = mapped_column(CHAR(36), ForeignKey("role.id", ondelete="CASCADE"), primary_key=True)