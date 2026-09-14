import uuid

from sqlalchemy import String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base
from models.instance import Instance


class Item(Base):
    __tablename__ = "item"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    instance_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("instance.id"),
        nullable=False,
    )

    uri: Mapped[str | None] = mapped_column(
        String(500),
        unique=True,
        nullable=True,
        index=True,
    )

    barcode: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        unique=True,
    )

    location: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    call_number: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    status: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    instance: Mapped["Instance"] = relationship(
        back_populates="items"
    )