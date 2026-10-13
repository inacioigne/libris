"""PostgreSQL editorial state, conditional writes and transaction-scoped write gate."""

from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKeyConstraint, String, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from libris.infrastructure.database import Base
from libris.modules.bibliographic.domain.editorial import EditorialRecord, EditorialState
from libris.modules.bibliographic.domain.errors import CatalogCode, CatalogError
from libris.modules.bibliographic.domain.models import ResourceIdentity, StaleRevisionError
from libris.modules.bibliographic.infrastructure.persistence import SemanticResource

# Stable namespace key. Shared for content writers; exclusive for editorial decisions.
WRITE_GATE = 0x4C4942524953
EDITORIAL_CHECKS = {
    "ck_editorial_positive": "version > 0 AND current_revision > 0",
    "ck_editorial_state": "editorial_state IN "
    "('draft','in_review','approved','published','withdrawn','archived')",
    "ck_editorial_pointers": "(approved_revision IS NULL OR "
    "approved_revision BETWEEN 1 AND current_revision) AND (published_revision IS NULL OR "
    "published_revision BETWEEN 1 AND current_revision)",
    "ck_editorial_public": "(editorial_state IN ('published','withdrawn','archived') AND "
    "published_revision IS NOT NULL) OR (editorial_state IN ('draft','in_review','approved') "
    "AND published_revision IS NULL)",
    "ck_editorial_candidate": "(candidate_state IS NULL AND (editorial_state NOT IN "
    "('published','withdrawn') OR current_revision = published_revision)) OR "
    "(candidate_state IS NOT NULL AND candidate_state IN ('draft','in_review','approved') "
    "AND editorial_state IN ('published','withdrawn') AND current_revision <> published_revision)",
    "ck_editorial_approval": "COALESCE((CASE WHEN COALESCE(candidate_state,editorial_state) "
    "= 'approved' THEN approved_revision = current_revision "
    "WHEN COALESCE(candidate_state,editorial_state) IN ('draft','in_review') "
    "THEN approved_revision IS NULL WHEN candidate_state IS NULL AND editorial_state "
    "IN ('published','withdrawn') THEN approved_revision = published_revision "
    "ELSE approved_revision IS NULL END), false)",
}


class SemanticEditorialState(Base):
    __tablename__ = "experimental_semantic_editorial_states"
    __table_args__ = (
        *(CheckConstraint(expression, name=name) for name, expression in EDITORIAL_CHECKS.items()),
        *(
            ForeignKeyConstraint(
                ["resource_id", field],
                [
                    "experimental_semantic_revisions.resource_id",
                    "experimental_semantic_revisions.number",
                ],
                name=f"fk_editorial_{field}",
            )
            for field in ("current_revision", "approved_revision", "published_revision")
        ),
    )
    resource_id: Mapped[UUID] = mapped_column(primary_key=True)
    editorial_state: Mapped[str] = mapped_column(String)
    version: Mapped[int]
    current_revision: Mapped[int]
    approved_revision: Mapped[int | None]
    published_revision: Mapped[int | None]
    candidate_state: Mapped[str | None] = mapped_column(String)


async def write_gate(session: AsyncSession, *, editorial: bool = False) -> None:
    function = "pg_advisory_xact_lock" if editorial else "pg_advisory_xact_lock_shared"
    await session.execute(text(f"SELECT {function}(:key)"), {"key": WRITE_GATE})


class EditorialStore:
    async def lock_resource(self, session: AsyncSession, identifier: UUID) -> SemanticResource:
        resource = await session.scalar(
            select(SemanticResource)
            .where(SemanticResource.id == identifier)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if resource is None:
            raise StaleRevisionError("Recurso ausente; recarregue o registro.")
        return resource

    async def get(self, session: AsyncSession, identifier: UUID) -> EditorialRecord | None:
        row = (
            await session.execute(
                select(
                    SemanticEditorialState, SemanticResource.uri, SemanticResource.current_revision
                )
                .join(SemanticResource, SemanticResource.id == SemanticEditorialState.resource_id)
                .where(SemanticEditorialState.resource_id == identifier)
                .execution_options(populate_existing=True)
            )
        ).one_or_none()
        if row is None:
            return None
        state, uri, current = row
        if current != state.current_revision:
            raise CatalogError(CatalogCode.REVISION_STALE, "Estado e conteúdo divergentes.")
        return EditorialRecord(
            identity=ResourceIdentity(identifier, uri),
            current_revision=state.current_revision,
            editorial_state=EditorialState(state.editorial_state),
            version=state.version,
            approved_revision=state.approved_revision,
            published_revision=state.published_revision,
            candidate_state=EditorialState(state.candidate_state)
            if state.candidate_state
            else None,
        )

    def values(self, record: EditorialRecord) -> dict[str, object]:
        return {
            "editorial_state": record.editorial_state,
            "version": record.version,
            "current_revision": record.current_revision,
            "approved_revision": record.approved_revision,
            "published_revision": record.published_revision,
            "candidate_state": record.candidate_state,
        }

    async def initialize(
        self, session: AsyncSession, resource: SemanticResource
    ) -> EditorialRecord:
        # Caller holds the resource row lock (or has inserted a new resource).
        record = await self.get(session, resource.id)
        if record is None:
            record = EditorialRecord(
                ResourceIdentity(resource.id, resource.uri),
                current_revision=resource.current_revision,
            )
            session.add(SemanticEditorialState(resource_id=resource.id, **self.values(record)))
            await session.flush()
        return record

    async def save(
        self, session: AsyncSession, before: EditorialRecord, after: EditorialRecord
    ) -> None:
        if after.identity != before.identity or after.version != before.version + 1:
            raise ValueError("CAS editorial deve preservar identidade e incrementar versão.")
        identifier = await session.scalar(
            update(SemanticEditorialState)
            .where(
                SemanticEditorialState.resource_id == before.identity.internal_id,
                SemanticEditorialState.version == before.version,
                SemanticEditorialState.current_revision == before.current_revision,
            )
            .values(**self.values(after))
            .returning(SemanticEditorialState.resource_id)
        )
        if identifier is None:
            raise CatalogError(CatalogCode.EDITORIAL_VERSION_STALE, "Conflito CAS editorial.")
