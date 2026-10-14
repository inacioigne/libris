"""Native JSON-line logging adapter. Emission is not a durable commit."""

import logging

from libris.modules.security_audit.domain.events import SecurityEvent


class LoggingSecuritySink:
    def __init__(self) -> None:
        self.logger = logging.getLogger("libris.security_audit.events")
        # A dedicated handler avoids application debug formatters/exception fields.
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(message)s"))
            self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

    def emit(self, event: SecurityEvent) -> None:
        self.logger.info(event.serialize())
