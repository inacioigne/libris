"""Stable domain codes; HTTP mappings belong to the API layer."""

from enum import StrEnum


class CatalogCode(StrEnum):
    MALFORMED_REQUEST = "request.malformed"
    SCHEMA_INVALID = "schema.invalid"
    REQUIRED = "schema.required"
    CARDINALITY = "schema.cardinality"
    VALUE = "schema.value"
    SHACL = "shacl.violation"
    MIN_COUNT = "shacl.min_count"
    MAX_COUNT = "shacl.max_count"
    QUALIFIED_MIN_COUNT = "shacl.qualified_min_count"
    QUALIFIED_MAX_COUNT = "shacl.qualified_max_count"
    DATATYPE = "shacl.datatype"
    NODE_KIND = "shacl.node_kind"
    CLASS = "shacl.class"
    IN = "shacl.in"
    PROFILE_UNKNOWN = "profile.unknown"
    PROFILE_INCOMPATIBLE = "profile.incompatible"
    PROFILE_UNAVAILABLE = "profile.unavailable"
    PROFILE_POLICY = "profile.policy"
    IDENTITY_INVALID = "identity.invalid"
    REFERENCE_INVALID = "reference.invalid"
    REFERENCE_UNVERIFIED = "reference.unverified"
    REFERENCE_DEPRECATED = "reference.deprecated"
    VOCABULARY_MISMATCH = "reference.vocabulary_mismatch"
    VOCABULARY_UNVERIFIED = "reference.vocabulary_unverified"
    RESOLVER_UNAVAILABLE = "reference.resolver_unavailable"
    RESOURCE_UNKNOWN = "resource.unknown"
    CONFLICT = "state.conflict"
    REVISION_STALE = "revision.stale"
    PRECONDITION_REQUIRED = "revision.precondition_required"
    VALIDATION_REJECTED = "validation.rejected"
    VALIDATOR_FAILURE = "validator.failure"
    INFRASTRUCTURE_UNAVAILABLE = "infrastructure.unavailable"
    INTERNAL = "internal.failure"
    EDITORIAL_STATE_INVALID = "editorial.state_invalid"
    TRANSITION_FORBIDDEN = "editorial.transition_forbidden"
    EDITORIAL_PERMISSION_DENIED = "editorial.permission_denied"
    EDITORIAL_PRECONDITION = "editorial.precondition_required"
    CONTENT_NOT_PUBLISHABLE = "editorial.content_not_publishable"
    EDITORIAL_VERSION_STALE = "editorial.version_stale"
    APPROVAL_STALE = "editorial.approval_stale"
    IDENTITY_OPERATION_INVALID = "identity.operation_invalid"


class CatalogError(ValueError):
    """Typed rejection, retaining compatibility with existing ValueError callers."""

    def __init__(self, code: CatalogCode, message: str) -> None:
        super().__init__(message)
        self.code = code


class ResourceNotFoundError(LookupError):
    """Missing stored resource/revision; distinguish from programming KeyError."""
