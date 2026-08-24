
from core.db import Base
import uuid

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey, String

class WorkLanguage(Base):
    __tablename__ = "work_language"

    work_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("work.id", ondelete="CASCADE"),
        primary_key=True,
    )

    language: Mapped[str] = mapped_column(
        String(35),
        primary_key=True,
    )

    work: Mapped["Work"] = relationship(
        back_populates="languages",
    )