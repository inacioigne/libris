import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base

if TYPE_CHECKING:
    from models.agent import Agent
    from models.item import Item
    from models.work import Work


class Instance(Base):
    __tablename__ = "instance"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    work_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("work.id"), nullable=False)
    publisher_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("agent.id"), nullable=True)
    isbn: Mapped[str] = mapped_column(String(30), nullable=True)
    publication_year: Mapped[int] = mapped_column(Integer, nullable=True)
    formato: Mapped[str] = mapped_column(String(50), nullable=True)

    work: Mapped["Work"] = relationship(back_populates="instances")
    publisher: Mapped["Agent | None"] = relationship(back_populates="published_instances")
    items: Mapped[list["Item"]] = relationship(back_populates="instance", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Instance {self.isbn!r}>"