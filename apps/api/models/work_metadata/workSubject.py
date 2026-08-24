import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base

if TYPE_CHECKING:
    from models.agent import Agent
    from models.work import Work

    
class WorkSubject(Base):
    __tablename__ = "work_subject"

    work_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("work.id", ondelete="CASCADE"),
        primary_key=True,
    )

    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subject.id"),
        primary_key=True,
    )

    sequence: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    work: Mapped["Work"] = relationship(
        back_populates="subjects",
    )

    subject: Mapped["Subject"] = relationship(
        back_populates="works",
    )