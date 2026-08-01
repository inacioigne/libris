import uuid

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base
from models.instance import Instance

class Work(Base):
    __tablename__ = "work"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=True)
    
    subjects: Mapped[list["WorkSubject"]] = relationship(
        back_populates="work",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    instances: Mapped[list["Instance"]] = relationship(
        back_populates="work",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    agents: Mapped[list["WorkAgent"]] = relationship(
        back_populates="work",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    def __repr__(self) -> str:
        return f"<Work {self.title!r}>"