"""Pydantic v2 catalogographic DTOs, independent of persistence and HTTP."""

# from .agent import AgentCreate, AgentRead, AgentUpdate
# from .instance import InstanceCreate, InstanceRead, InstanceUpdate
# from .item import ItemCreate, ItemRead, ItemUpdate
# from .subject import SubjectCreate, SubjectRead, SubjectUpdate
from .work import WorkCreate
# , WorkRead, WorkUpdate

__all__ = [
    "WorkCreate",
    # "WorkRead",
    # "WorkUpdate",
    # "InstanceCreate",
    # "InstanceRead",
    # "InstanceUpdate",
    # "ItemCreate",
    # "ItemRead",
    # "ItemUpdate",
    # "AgentCreate",
    # "AgentRead",
    # "AgentUpdate",
    # "SubjectCreate",
    # "SubjectRead",
    # "SubjectUpdate",
]

# from .relationships import (
#     RelationshipCreate,
#     RelationshipRead,
#     RelationshipReplace,
#     RelationshipUpdate,
# )

__all__ += [
    "RelationshipCreate",
    "RelationshipRead",
    "RelationshipReplace",
    "RelationshipUpdate",
]
