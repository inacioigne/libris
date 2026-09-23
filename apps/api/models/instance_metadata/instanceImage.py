from core.db import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy import Boolean, String, Integer, ForeignKey
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from models.instance_metadata.instance import Instance

    

class InstanceImage(Base):
    __tablename__ = "instance_image"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    instance_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("instance.id"),
        nullable=False,
        index=True,
    )

    uri: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )

    source: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    image_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="front_cover",
    )

    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    instance: Mapped["Instance"] = relationship(
        back_populates="images"
    )