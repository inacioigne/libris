from core.db import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey, String

class WorkTypeAssignment(Base):
    __tablename__ = "work_type"

    work_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("work.id", ondelete="CASCADE"),
        primary_key=True,
    )

    type: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )

    work: Mapped["Work"] = relationship(
        back_populates="types",
    )