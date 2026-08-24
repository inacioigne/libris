import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base


class WorkGenre(Base):
    __tablename__ = "work_genre"

    __table_args__ = (
        UniqueConstraint(
            "work_id",
            "value",
            name="uq_work_genre_work_value",
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

    value: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    sequence: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    work: Mapped["Work"] = relationship(
        back_populates="genres",
    )

    def __repr__(self) -> str:
        return f"<WorkGenre {self.value!r}>"