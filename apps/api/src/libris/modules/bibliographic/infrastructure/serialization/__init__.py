"""Public semantic representation API, version 1.0; no persistence or HTTP calls."""

from .adapters import ResourceCreate, ResourceUpdate, apply_update, create_to_graph
from .mapping import ReferenceMapping, ResourceRead, resource_to_graph
from .negotiation import MEDIA_TYPES, NotAcceptable, RepresentationFormat, negotiate_format
from .projection import graph_to_read
from .representation import (
    CONTEXT_VERSION,
    CONTRACT_VERSION,
    SemanticFormat,
    context_digest,
    local_context,
    parse_representation,
    serialize_composed,
    serialize_graph,
    serialize_resource,
)

__all__ = [
    "CONTEXT_VERSION",
    "CONTRACT_VERSION",
    "MEDIA_TYPES",
    "NotAcceptable",
    "ReferenceMapping",
    "RepresentationFormat",
    "ResourceRead",
    "ResourceCreate",
    "ResourceUpdate",
    "apply_update",
    "create_to_graph",
    "graph_to_read",
    "SemanticFormat",
    "context_digest",
    "local_context",
    "negotiate_format",
    "parse_representation",
    "resource_to_graph",
    "serialize_composed",
    "serialize_graph",
    "serialize_resource",
]
