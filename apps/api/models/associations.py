import uuid

from sqlalchemy import Table, Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base

class WorkAgent(Base):
    __tablename__ = "work_agent"

    work_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("work.id"), primary_key=True)
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agent.id"), primary_key=True)
    role: Mapped[str] = mapped_column(String(50), nullable=True)

    work: Mapped["Work"] = relationship(back_populates="agents")
    agent: Mapped["Agent"] = relationship(back_populates="works")