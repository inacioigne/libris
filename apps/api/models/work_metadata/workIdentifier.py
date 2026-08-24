import uuid
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from core.db import Base

class WorkIdentifier(Base):
    __tablename__ = "work_identifier"

    __table_args__ = (
        UniqueConstraint(
            "work_id",
            "type",
            "value",
            name="uq_work_identifier",
        ),
    )

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

    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    value: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    uri: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    source: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    work: Mapped["Work"] = relationship(
        back_populates="identifiers",
    )