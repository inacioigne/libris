from core.db import Base
import uuid
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

class WorkRelation(Base):
    __tablename__ = "work_relation"

    __table_args__ = (
        UniqueConstraint(
            "source_work_id",
            "target_work_id",
            "relation_type",
            name="uq_work_relation",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    source_work_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("work.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    target_work_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("work.id"),
        nullable=False,
        index=True,
    )

    relation_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    source_work: Mapped["Work"] = relationship(
        foreign_keys=[source_work_id],
        back_populates="outgoing_relations",
    )

    target_work: Mapped["Work"] = relationship(
        foreign_keys=[target_work_id],
        back_populates="incoming_relations",
    )