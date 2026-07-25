import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base
from models.associations import WorkAgent

if TYPE_CHECKING:
    from models.instance import Instance


class Agent(Base):
    __tablename__ = "agent"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=True)  
    identifier: Mapped[str] = mapped_column(String(255), nullable=True)  

    works: Mapped[list["WorkAgent"]] = relationship(back_populates="agent")
    published_instances: Mapped[list["Instance"]] = relationship(back_populates="publisher")

    def __repr__(self) -> str:
        return f"<Agent {self.name!r}>"