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
    RESOURCE_UNKNOWN = "resource.unknown"
    CONFLICT = "state.conflict"
    REVISION_STALE = "revision.stale"
    PRECONDITION_REQUIRED = "revision.precondition_required"
    VALIDATION_REJECTED = "validation.rejected"
    VALIDATOR_FAILURE = "validator.failure"
    INFRASTRUCTURE_UNAVAILABLE = "infrastructure.unavailable"
    INTERNAL = "internal.failure"


class CatalogError(ValueError):
    """Typed rejection, retaining compatibility with existing ValueError callers."""

    def __init__(self, code: CatalogCode, message: str) -> None:
        super().__init__(message)
        self.code = code


class ResourceNotFoundError(LookupError):
    """Missing stored resource/revision; distinguish from programming KeyError."""
