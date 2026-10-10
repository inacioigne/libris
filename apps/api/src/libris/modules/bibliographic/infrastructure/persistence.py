from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKeyConstraint, String, select, update
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from libris.infrastructure.database import Base
from libris.modules.bibliographic.domain.models import (
    Provenance,
    ResourceIdentity,
    Revision,
    StaleRevisionError,
)


class SemanticResource(Base):
    __tablename__ = "experimental_semantic_resources"
    __table_args__ = (
        CheckConstraint("current_revision > 0", name="ck_semantic_current_positive"),
        ForeignKeyConstraint(
            ["id", "current_revision"],
            [
                "experimental_semantic_revisions.resource_id",
                "experimental_semantic_revisions.number",
            ],
            name="fk_semantic_current",
            use_alter=True,
            deferrable=True,
            initially="DEFERRED",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    uri: Mapped[str] = mapped_column(String, unique=True)
    current_revision: Mapped[int]


class SemanticRevision(Base):
    __tablename__ = "experimental_semantic_revisions"
    __table_args__ = (
        ForeignKeyConstraint(["resource_id"], ["experimental_semantic_resources.id"]),
        CheckConstraint("number > 0", name="ck_semantic_revision_positive"),
        CheckConstraint("jsonb_typeof(document) = 'array'", name="ck_semantic_document_array"),
        CheckConstraint("length(trim(source)) > 0", name="ck_semantic_source"),
        CheckConstraint("length(trim(process)) > 0", name="ck_semantic_process"),
    )
    resource_id: Mapped[UUID] = mapped_column(primary_key=True)
    number: Mapped[int] = mapped_column(primary_key=True)
    document: Mapped[list[dict[str, object]]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source: Mapped[str] = mapped_column(String)
    process: Mapped[str] = mapped_column(String)
    profile: Mapped[str] = mapped_column(String)
    actor_id: Mapped[str | None] = mapped_column(String, nullable=True)


class RevisionStore:
    async def create(self, session: AsyncSession, identity: ResourceIdentity) -> None:
        session.add(SemanticResource(id=identity.internal_id, uri=identity.uri, current_revision=1))
        await session.flush()

    async def advance(self, session: AsyncSession, identifier: UUID, expected: int) -> str:
        if expected < 1:
            raise ValueError("A revisão esperada deve ser positiva.")
        uri = await session.scalar(
            update(SemanticResource)
            .where(SemanticResource.id == identifier, SemanticResource.current_revision == expected)
            .values(current_revision=expected + 1)
            .returning(SemanticResource.uri)
        )
        if uri is None:
            raise StaleRevisionError("Recurso ausente ou revisão obsoleta; recarregue o registro.")
        return uri

    async def save(
        self, session: AsyncSession, revision: Revision, document: list[dict[str, object]]
    ) -> None:
        session.add(
            SemanticRevision(
                resource_id=revision.identity.internal_id,
                number=revision.number,
                document=document,
                created_at=revision.created_at,
                source=revision.provenance.source,
                process=revision.provenance.process,
                profile=revision.profile,
                actor_id=revision.actor_id,
            )
        )
        await session.flush()

    async def get(
        self, session: AsyncSession, identifier: UUID, number: int | None
    ) -> tuple[Revision, list[dict[str, object]]]:
        statement = (
            select(SemanticResource, SemanticRevision)
            .join(SemanticRevision, SemanticResource.id == SemanticRevision.resource_id)
            .where(SemanticResource.id == identifier)
        )
        statement = statement.where(
            SemanticRevision.number
            == (SemanticResource.current_revision if number is None else number)
        )
        row = (await session.execute(statement)).one_or_none()
        if row is None:
            raise LookupError("Recurso ou revisão não encontrado.")
        resource, stored = row
        revision = Revision(
            ResourceIdentity(resource.id, resource.uri),
            stored.number,
            stored.created_at,
            Provenance(stored.source, stored.process),
            stored.profile,
            stored.actor_id,
        )
        return revision, stored.document
