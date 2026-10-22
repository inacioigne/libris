"""One correlation ID per request; services remain usable outside HTTP."""

from contextvars import ContextVar

request_id_context: ContextVar[str | None] = ContextVar("request_id", default=None)
