import uuid

from sqlalchemy import String, Boolean
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import Mapped, mapped_column

from core.db import Base


class User(Base):
    __tablename__ = "user"

    id: Mapped[uuid.UUID] = mapped_column(
        CHAR(36),
        primary_key=True,
        default=uuid.uuid4,
    )

    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )