from core.db import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String


class Subject(Base):
    __tablename__ = "subject"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    preferred_label: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    works: Mapped[list["WorkSubject"]] = relationship(
        back_populates="subject",
        cascade="all, delete-orphan",
    )