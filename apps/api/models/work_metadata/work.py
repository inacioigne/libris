import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base

if TYPE_CHECKING:
    from models.instance import Instance
    from models.work_metadata import (
        WorkTitle,
        WorkLanguage,
        WorkGenre,
        WorkNote,
        WorkIdentifier,
        WorkRelation,
        WorkTypeAssignment,
        WorkAgent,
        WorkSubject
    )
    # from models.associations import WorkAgent, WorkSubject


class Work(Base):
    __tablename__ = "work"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Título preferido desnormalizado para consultas rápidas.
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    uri: Mapped[str | None] = mapped_column(
        String(500),
        unique=True,
        nullable=True,
        index=True,
    )

    titles: Mapped[list["WorkTitle"]] = relationship(
        back_populates="work",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="WorkTitle.sequence",
    )

    types: Mapped[list["WorkTypeAssignment"]] = relationship(
        back_populates="work",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    languages: Mapped[list["WorkLanguage"]] = relationship(
        back_populates="work",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    genres: Mapped[list["WorkGenre"]] = relationship(
        back_populates="work",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="WorkGenre.sequence",
    )

    notes: Mapped[list["WorkNote"]] = relationship(
        back_populates="work",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    identifiers: Mapped[list["WorkIdentifier"]] = relationship(
        back_populates="work",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    outgoing_relations: Mapped[list["WorkRelation"]] = relationship(
        foreign_keys="WorkRelation.source_work_id",
        back_populates="source_work",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    incoming_relations: Mapped[list["WorkRelation"]] = relationship(
        foreign_keys="WorkRelation.target_work_id",
        back_populates="target_work",
        lazy="selectin",
    )

    subjects: Mapped[list["WorkSubject"]] = relationship(
        back_populates="work",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    agents: Mapped[list["WorkAgent"]] = relationship(
        back_populates="work",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    instances: Mapped[list["Instance"]] = relationship(
        back_populates="work",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Work {self.title!r}>"