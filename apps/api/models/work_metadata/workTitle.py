import uuid
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from core.db import Base

class WorkTitle(Base):
    __tablename__ = "work_title"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    work_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("work.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    value: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    language: Mapped[str | None] = mapped_column(
        String(35),
        nullable=True,
    )

    title_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="main",
    )

    is_preferred: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )

    sequence: Mapped[int] = mapped_column(
        default=1,
        nullable=False,
    )

    work: Mapped["Work"] = relationship(
        back_populates="titles",
    )