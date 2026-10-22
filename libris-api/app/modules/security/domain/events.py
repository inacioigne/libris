"""Security envelope v1; deliberately independent of catalogographic history."""

import json
import re
from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modules.identity.domain.authorization import Operation, ResourceKind 
from app.modules.identity.domain.permissions import Permission


class EventType(StrEnum):
    AUTHENTICATION_SUCCEEDED = "authentication.succeeded"
    AUTHENTICATION_FAILED = "authentication.failed"
    AUTHORIZATION_GRANTED = "authorization.granted"
    AUTHORIZATION_DENIED = "authorization.denied"


class Outcome(StrEnum):
    SUCCESS = "success"
    DENIED = "denied"
    ERROR = "error"
    UNAVAILABLE = "unavailable"


class ActorType(StrEnum):
    HUMAN = "human"
    TECHNICAL = "technical"
    UNKNOWN = "unknown"


class Action(StrEnum):
    AUTHENTICATE = "identity.authenticate"
    PERMISSION_CHECK = "identity.permission_check"
    UNKNOWN_OPERATION = "identity.unknown_operation"


class Reason(StrEnum):
    NONE = "none"
    MISSING_BEARER = "missing_bearer"
    MALFORMED_BEARER = "malformed_bearer"
    INVALID_TOKEN = "invalid_token"
    CLIENT_NOT_ALLOWED = "client_not_allowed"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    INVALID_OPERATION_RESOURCE = "invalid_operation_resource"
    UNPUBLISHED_PROJECTION = "unpublished_projection"
    MISSING_CONTEXT = "missing_context"
    INVALID_CONTEXT = "invalid_context"
    TECHNICAL_SCOPE = "technical_scope"
    INSUFFICIENT_PERMISSIONS = "insufficient_permissions"


class SecurityEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0"] = "1.0"
    event_id: UUID = Field(default_factory=uuid4)
    event_type: EventType
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    correlation_id: UUID
    actor_id: str | None = None
    actor_type: ActorType = ActorType.UNKNOWN
    action: Operation | Action
    outcome: Outcome
    reason: Reason = Reason.NONE
    required_permissions: tuple[Permission, ...] = ()
    resource_type: ResourceKind | None = None
    resource_id: UUID | None = None
    component: Literal["api", "authorization"]

    @field_validator("occurred_at")
    @classmethod
    def utc_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Timezone required")
        return value.astimezone(UTC)

    @field_validator("actor_id")
    @classmethod
    def opaque_actor(cls, value: str | None) -> str | None:
        if value is not None and not re.fullmatch(
            r"oidc:sha256:[0-9a-f]{64}|(?:service|automated):[a-z][a-z0-9_.-]{0,63}", value
        ):
            raise ValueError("Opaque actor required")
        return value

    @model_validator(mode="after")
    def actor_consistency(self) -> "SecurityEvent":
        if (self.actor_id is None) != (self.actor_type == ActorType.UNKNOWN):
            raise ValueError("Unknown actor must be null")
        if self.actor_id is not None:
            human = self.actor_id.startswith("oidc:sha256:")
            if human != (self.actor_type == ActorType.HUMAN):
                raise ValueError("Actor type mismatch")
        success = self.event_type in {
            EventType.AUTHENTICATION_SUCCEEDED,
            EventType.AUTHORIZATION_GRANTED,
        }
        if success != (self.outcome == Outcome.SUCCESS):
            raise ValueError("Event/outcome mismatch")
        if self.event_type == EventType.AUTHENTICATION_FAILED and self.actor_id is not None:
            raise ValueError("Failed authentication cannot establish an actor")
        if (
            self.event_type == EventType.AUTHENTICATION_SUCCEEDED
            and self.actor_type != ActorType.HUMAN
        ):
            raise ValueError("Authenticated human required")
        return self

    def serialize(self) -> str:
        return json.dumps(self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
