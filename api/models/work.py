import uuid

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base
from models.agent import Agent
from models.instance import Instance
# from .associations import work_agent


class Work(Base):
    __tablename__ = "work"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=True)
    subject: Mapped[str] = mapped_column(String(100), nullable=True)

    instances: Mapped[list["Instance"]] = relationship(back_populates="work", cascade="all, delete-orphan")
    agents: Mapped[list["WorkAgent"]] = relationship(
        back_populates="work",
        cascade="all, delete-orphan"
    )
    def __repr__(self) -> str:
        return f"<Work {self.title!r}>"