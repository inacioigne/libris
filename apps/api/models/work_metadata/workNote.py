from core.db import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey, String, Text

class WorkNote(Base):
    __tablename__ = "work_note"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    work_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("work.id", ondelete="CASCADE"),
        nullable=False,
    )

    value: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    note_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    sequence: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    work: Mapped["Work"] = relationship(
        back_populates="notes",
    )