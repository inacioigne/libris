"""Trusted actor selection and envelopes for existing content/editorial contracts."""

from uuid import uuid4

from libris.modules.bibliographic.domain.audit import (
    ActorType,
    AuditEvent,
    AuditEventType,
    ExecutionActor,
    RestorationKind,
)
from libris.modules.bibliographic.domain.editorial import (
    EditorialOperation,
    PreparedEditorialEvent,
)
from libris.modules.bibliographic.domain.models import Provenance, Revision
from libris.modules.identity.domain.models import AuthenticatedActor, actor_identifier


def audit_actor(
    actor: AuthenticatedActor | None,
    execution_actor: ExecutionActor | None = None,
) -> tuple[str | None, ActorType | None]:
    if actor is not None and execution_actor is not None:
        raise ValueError("Operação deve ter um único contexto de ator.")
    if actor is not None:
        if (
            not isinstance(actor, AuthenticatedActor)
            or actor.actor_id != actor_identifier(actor.issuer, actor.subject)
            or not actor.subject.strip()
        ):
            raise ValueError("Identidade humana deve vir do contexto OIDC validado.")
        return actor.actor_id, ActorType.HUMAN
    if execution_actor is not None:
        if not isinstance(execution_actor, ExecutionActor):
            raise ValueError("Contexto técnico deve ser configurado pelo servidor.")
        return execution_actor.actor_id, execution_actor.actor_type
    return None, None


def content_event(
    revision: Revision,
    event_type: AuditEventType,
    actor_type: ActorType | None,
    *,
    source_revision: int | None = None,
) -> AuditEvent:
    return AuditEvent(
        event_id=uuid4(),
        event_type=event_type,
        identity=revision.identity,
        revision_number=revision.number,
        occurred_at=revision.created_at,
        source=revision.provenance.source,
        process=revision.provenance.process,
        profile=revision.profile,
        actor_id=revision.actor_id,
        actor_type=actor_type,
        reason=revision.provenance.reason,
        source_revision=source_revision,
        restoration_kind=RestorationKind.CONTENT if source_revision is not None else None,
    )


def editorial_event(
    prepared: PreparedEditorialEvent,
    revision: Revision,
    provenance: Provenance,
    *,
    actor: AuthenticatedActor,
) -> AuditEvent:
    """Prepare only; future state adapter must append in the SAME CAS transaction.

    RETURN and ARCHIVE deliberately have no misleading mapping to the eight-event
    taxonomy. Their durable integration requires a governed extension of it.
    """
    identifier, kind = audit_actor(actor)
    if (
        prepared.actor_id != identifier
        or prepared.identity != revision.identity
        or (prepared.revision != revision.number)
    ):
        raise ValueError("Evento preparado diverge do contexto/revisão selecionados.")
    types = {
        EditorialOperation.SUBMIT: AuditEventType.SUBMITTED,
        EditorialOperation.APPROVE: AuditEventType.APPROVED,
        EditorialOperation.PUBLISH: AuditEventType.PUBLISHED,
        EditorialOperation.WITHDRAW: AuditEventType.WITHDRAWN,
        EditorialOperation.REPUBLISH: AuditEventType.RESTORED,
    }
    if prepared.operation not in types:
        raise ValueError("Operação editorial ainda sem evento na taxonomia versionada.")
    if provenance.reason is not None and provenance.reason != prepared.justification:
        raise ValueError("Justificativas editoriais divergentes.")
    return AuditEvent(
        event_id=uuid4(),
        event_type=types[prepared.operation],
        identity=prepared.identity,
        revision_number=prepared.revision,
        occurred_at=prepared.occurred_at,
        source=provenance.source,
        process=provenance.process,
        profile=revision.profile,
        actor_id=identifier,
        actor_type=kind,
        reason=prepared.justification,
        previous_state=prepared.previous_state,
        new_state=prepared.next_state,
        scope=prepared.scope,
        previous_version=prepared.previous_version,
        new_version=prepared.next_version,
        restoration_kind=(
            RestorationKind.EDITORIAL
            if prepared.operation == EditorialOperation.REPUBLISH
            else None
        ),
    )
