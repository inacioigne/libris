"""Authorized internal history, distinct from trusted storage access and public RDF."""

import json
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from rdflib import Graph
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from libris.modules.bibliographic.application.comparison import SemanticDiff, compare_graphs
from libris.modules.bibliographic.domain.audit import AuditEvent
from libris.modules.bibliographic.domain.editorial import EditorialRecord
from libris.modules.bibliographic.domain.models import Revision
from libris.modules.bibliographic.infrastructure.audit import (
    AuditStore,
)
from libris.modules.bibliographic.infrastructure.editorial import EditorialStore, write_gate
from libris.modules.bibliographic.infrastructure.persistence import (
    RevisionStore,
)
from libris.modules.bibliographic.infrastructure.rdf import parse_document
from libris.modules.identity.application.authorization import (
    AuthorizationGuard,
    ExecutionContext,
    execution_context,
)
from libris.modules.identity.domain.authorization import Operation as O
from libris.modules.identity.domain.authorization import ResourceContext
from libris.modules.identity.domain.authorization import ResourceKind as K
from libris.modules.identity.domain.models import AuthenticatedActor
from libris.modules.identity.domain.permissions import Permission


@dataclass(frozen=True)
class RevisionHistoryEntry:
    revision: Revision
    # False means no observed content event, never a synthesized legacy event.
    content_event_recorded: bool


@dataclass(frozen=True)
class EditorialHistory:
    # None explicitly means a legacy resource with no observed editorial initialization.
    state: EditorialRecord | None
    current: Revision
    events: tuple[AuditEvent, ...]


class HistoryService:
    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        *,
        authorization: AuthorizationGuard | None = None,
    ) -> None:
        self.authorization = authorization or AuthorizationGuard()
        self.sessions = sessions
        self.revisions = RevisionStore()
        self.audit = AuditStore()

    def _authorize(
        self,
        actor: AuthenticatedActor | None,
        permission: Permission,
        context: ExecutionContext | None = None,
        resource_id: UUID | None = None,
    ) -> None:
        operation = {
            Permission.METADATA_REVISION_READ: O.METADATA_REVISION_READ,
            Permission.METADATA_AUDIT_READ: O.METADATA_AUDIT_READ,
        }[permission]
        self.authorization.require(
            context=execution_context(context, actor),
            operation=operation,
            resource=ResourceContext(K.METADATA, resource_id=resource_id),
        )

    async def read_revision(
        self,
        identifier: UUID,
        number: int | None = None,
        *,
        actor: AuthenticatedActor | None = None,
        context: ExecutionContext | None = None,
    ) -> tuple[Revision, Graph]:
        self._authorize(actor, Permission.METADATA_REVISION_READ, context, identifier)
        if number is not None and (type(number) is not int or number < 1):
            raise ValueError("Revisão deve ser positiva.")
        async with self.sessions() as session:
            revision, document = await self.revisions.get(session, identifier, number)
        return revision, parse_document(json.dumps(document), "json-ld")

    async def list_revisions(
        self,
        identifier: UUID,
        *,
        actor: AuthenticatedActor | None = None,
        context: ExecutionContext | None = None,
        limit: int = 100,
        after_number: int = 0,
    ) -> tuple[RevisionHistoryEntry, ...]:
        self._authorize(actor, Permission.METADATA_REVISION_READ, context, identifier)
        async with self.sessions() as session:
            revisions = await self.revisions.list(
                session,
                identifier,
                limit=limit,
                after_number=after_number,
            )
            recorded = await self.audit.content_revision_numbers(
                session,
                identifier,
                tuple(revision.number for revision in revisions),
            )
        return tuple(
            RevisionHistoryEntry(revision, revision.number in recorded) for revision in revisions
        )

    async def list_events(
        self,
        identifier: UUID,
        *,
        actor: AuthenticatedActor | None = None,
        context: ExecutionContext | None = None,
        limit: int = 100,
        after: tuple[datetime, UUID] | None = None,
    ) -> tuple[AuditEvent, ...]:
        self._authorize(actor, Permission.METADATA_AUDIT_READ, context, identifier)
        async with self.sessions() as session:
            return await self.audit.list(session, identifier, limit=limit, after=after)

    async def read_event(
        self,
        identifier: UUID,
        event_id: UUID,
        *,
        actor: AuthenticatedActor | None = None,
        context: ExecutionContext | None = None,
    ) -> AuditEvent:
        self._authorize(actor, Permission.METADATA_AUDIT_READ, context, identifier)
        async with self.sessions() as session:
            return await self.audit.get(session, identifier, event_id)

    async def compare_revisions(
        self,
        identifier: UUID,
        previous_number: int,
        current_number: int,
        *,
        actor: AuthenticatedActor | None = None,
        context: ExecutionContext | None = None,
    ) -> SemanticDiff:
        previous, current = (
            await self.read_revision(identifier, previous_number, actor=actor, context=context),
            await self.read_revision(identifier, current_number, actor=actor, context=context),
        )
        return compare_graphs(previous[1], current[1])

    async def read_editorial(
        self,
        identifier: UUID,
        *,
        actor: AuthenticatedActor | None = None,
        context: ExecutionContext | None = None,
        limit: int = 100,
        after: tuple[datetime, UUID] | None = None,
    ) -> EditorialHistory:
        self.authorization.require(
            context=execution_context(context, actor),
            operation=O.METADATA_EDITORIAL_HISTORY,
            resource=ResourceContext(K.METADATA, resource_id=identifier),
        )
        async with self.sessions() as session, session.begin():
            await write_gate(session)
            states = EditorialStore()
            await states.lock_resource(session, identifier)
            state = await states.get(session, identifier)
            current, _ = await self.revisions.get(session, identifier, None)
            events = await self.audit.list(session, identifier, limit=limit, after=after)
        return EditorialHistory(state, current, events)
