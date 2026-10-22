"""Best-effort observation never changes access decisions or business transactions."""

import logging
from typing import Protocol
from uuid import UUID, uuid4

from app.core.correlation import request_id_context

from app.modules.security.domain.events import SecurityEvent


class SecuritySink(Protocol):
    def emit(self, event: SecurityEvent) -> None: ...


def correlation_id() -> UUID:
    value = request_id_context.get()
    return UUID(value) if value is not None else uuid4()


def emit_safely(sink: SecuritySink, event: SecurityEvent) -> None:
    try:
        sink.emit(event)
    except Exception:
        # The sink is an external adapter boundary. Never include its exception,
        # event, traceback or credentials. Loss must be monitored operationally.
        logging.getLogger("libris.security_audit.failure").warning(
            "security_audit_sink_unavailable"
        )
