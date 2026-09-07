import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base

if TYPE_CHECKING:
    from models.agent import Agent
    from models.item import Item
    from api.models.work_metadata.work import Work
    
    
class Instance(Base):
    __tablename__ = "instance"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    work_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("work.id"),
        nullable=False,
    )

    # BIBFRAME: bf:identifiedBy
    isbn: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        unique=True,
    )

    # BIBFRAME: bf:provisionActivity / bf:agent
    publisher_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent.id"),
        nullable=True,
    )

    # BIBFRAME: bf:provisionActivity / bf:date
    publication_year: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # BIBFRAME: bf:provisionActivity / bf:place
    publication_place: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # BIBFRAME: bf:editionStatement
    edition: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # BIBFRAME: bf:carrier
    formato: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    
    carrier: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # BIBFRAME: bf:extent
    extent: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # BIBFRAME: bf:dimensions
    dimensions: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    work: Mapped["Work"] = relationship(
        back_populates="instances"
    )

    publisher: Mapped["Agent | None"] = relationship(
        back_populates="published_instances"
    )

    items: Mapped[list["Item"]] = relationship(
        back_populates="instance",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Instance {self.id}>"

