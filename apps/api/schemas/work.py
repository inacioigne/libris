import uuid
from enum import StrEnum
from typing import Annotated, Any

from pydantic import ConfigDict

from pydantic import (
    AnyHttpUrl,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
)


# ============================================================
# Shared types
# ============================================================

NonEmptyStr = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=255,
    ),
]


class WorkType(StrEnum):
    """
    BIBFRAME Work resource categories.

    These are intentionally represented as application-level
    values for now. Later they can be mapped to BIBFRAME URIs.
    """

    TEXT = "Text"
    CARTOGRAPHY = "Cartography"
    DATASET = "Dataset"
    AUDIO = "Audio"
    NOTATED_MUSIC = "NotatedMusic"
    NOTATED_MOVEMENT = "NotatedMovement"
    STILL_IMAGE = "StillImage"
    MOVING_IMAGE = "MovingImage"
    OBJECT = "Object"
    MULTIMEDIA = "Multimedia"
    MIXED_MATERIAL = "MixedMaterial"
    COLLECTION = "Collection"


class AgentRole(StrEnum):
    """
    Common contribution roles.

    This is deliberately not the complete BIBFRAME/RDA role
    vocabulary. It is an initial controlled vocabulary.
    """

    AUTHOR = "author"
    EDITOR = "editor"
    TRANSLATOR = "translator"
    ILLUSTRATOR = "illustrator"
    COMPOSER = "composer"
    PHOTOGRAPHER = "photographer"
    DIRECTOR = "director"
    CARTOGRAPHER = "cartographer"
    CONTRIBUTOR = "contributor"


class IdentifierType(StrEnum):
    ISBN = "isbn"
    ISSN = "issn"
    DOI = "doi"
    LCCN = "lccn"
    OCLC = "oclc"
    VIAF = "viaf"
    URI = "uri"
    LOCAL = "local"


# ============================================================
# Titles
# ============================================================

class WorkTitleCreate(BaseModel):
    """
    A structured BIBFRAME title.

    Keeping title as an entity-like structure allows us to support
    main, variant, parallel and translated titles without changing
    the Work model later.
    """

    value: NonEmptyStr

    language: str | None = Field(
        default=None,
        max_length=35,
        description="BCP 47 language tag, e.g. pt-BR, en, es.",
    )

    title_type: str = Field(
        default="main",
        max_length=50,
        description="main, variant, parallel, abbreviated, key, etc.",
    )

    is_preferred: bool = True


# ============================================================
# Agents / Contributions
# ============================================================

class WorkAgentCreate(BaseModel):
    """
    Relationship between a Work and an Agent.

    The Agent itself is referenced by UUID because Agents are
    first-class entities in the Libris domain.
    """

    agent_id: uuid.UUID

    role: AgentRole = AgentRole.CONTRIBUTOR

    primary: bool = False

    sequence: int | None = Field(
        default=None,
        ge=1,
        le=999,
    )


class WorkAgentRead(WorkAgentCreate):
    # work_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Subjects
# ============================================================

class WorkSubjectCreate(BaseModel):
    """
    Relationship between a Work and an existing Subject.
    """

    subject_id: uuid.UUID

    sequence: int | None = Field(
        default=None,
        ge=1,
        le=999,
    )


class WorkSubjectRead(WorkSubjectCreate):
    # work_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Identifiers
# ============================================================

class WorkIdentifierCreate(BaseModel):
    """
    External identifier associated with a Work.

    This is intentionally not stored directly in Work yet.
    It prepares the API for a dedicated identifier entity/table.
    """

    type: IdentifierType

    value: NonEmptyStr

    uri: AnyHttpUrl | None = None

    source: str | None = Field(
        default=None,
        max_length=100,
    )


# ============================================================
# Work relationships
# ============================================================

class WorkRelationType(StrEnum):
    TRANSLATION_OF = "translationOf"
    ADAPTATION_OF = "adaptationOf"
    REVISION_OF = "revisionOf"
    CONTINUATION_OF = "continuationOf"
    SUPPLEMENT_TO = "supplementTo"
    PREQUEL = "prequel"
    SEQUEL = "sequel"
    RELATED_TO = "relatedTo"


class WorkRelationCreate(BaseModel):
    """
    Relationship between two Works.

    This is fundamental for the Linked Data model and should
    eventually become a first-class relationship entity.
    """

    work_id: uuid.UUID

    relation_type: WorkRelationType


# ============================================================
# Work
# ============================================================

class WorkBase(BaseModel):
    """
    Common representation of a BIBFRAME Work.

    This schema represents the conceptual resource, not its
    physical/digital manifestation.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    title: NonEmptyStr

    titles: list[WorkTitleCreate] = Field( 
        default_factory=list,
        max_length=50,
    )

    types: list[WorkType] = Field(
        default_factory=list,
        min_length=1,
        max_length=10,
    )

    languages: list[
        Annotated[
            str,
            StringConstraints(
                strip_whitespace=True,
                min_length=2,
                max_length=35,
            ),
        ]
    ] = Field(
        default_factory=list,
        max_length=20,
        description="BCP 47 language tags.",
    )

    agents: list[WorkAgentCreate] = Field(
        default_factory=list,
        max_length=100,
    )

    subjects: list[WorkSubjectCreate] = Field(
        default_factory=list,
        max_length=100,
    )

    genres: list[
        Annotated[
            str,
            StringConstraints(
                strip_whitespace=True,
                min_length=1,
                max_length=255,
            ),
        ]
    ] = Field(
        default_factory=list,
        max_length=50,
    )

    summary: str | None = Field(
        default=None,
        max_length=5000,
    )

    notes: list[
        Annotated[
            str,
            StringConstraints(
                strip_whitespace=True,
                min_length=1,
                max_length=2000,
            ),
        ]
    ] = Field(
        default_factory=list,
        max_length=100,
    )

    identifiers: list[WorkIdentifierCreate] = Field(
        default_factory=list,
        max_length=50,
    )

    uri: AnyHttpUrl | None = Field(
        default=None,
        description="Canonical URI identifying the Work.",
    )

    relations: list[WorkRelationCreate] = Field(
        default_factory=list,
        max_length=100,
    )

    @field_validator("types")
    @classmethod
    def validate_types(
        cls,
        value: list[WorkType],
    ) -> list[WorkType]:
        """
        Avoid duplicate Work types.
        """

        if len(value) != len(set(value)):
            raise ValueError("Work types must be unique.")

        return value

    @field_validator("languages")
    @classmethod
    def validate_languages(
        cls,
        value: list[str],
    ) -> list[str]:
        """
        Normalize language tags.

        Full BCP 47 validation can be introduced later through
        a dedicated value object / library.
        """

        normalized = [
            language.replace("_", "-").lower()
            for language in value
        ]

        if len(normalized) != len(set(normalized)):
            raise ValueError("Languages must be unique.")

        return normalized

    @field_validator("agents")
    @classmethod
    def validate_agents(
        cls,
        value: list[WorkAgentCreate],
    ) -> list[WorkAgentCreate]:
        """
        The same Agent should not be linked to the same Work
        more than once.
        """

        agent_ids = [agent.agent_id for agent in value]

        if len(agent_ids) != len(set(agent_ids)):
            raise ValueError(
                "An agent cannot be associated with the same "
                "work more than once."
            )

        return value

    @field_validator("subjects")
    @classmethod
    def validate_subjects(
        cls,
        value: list[WorkSubjectCreate],
    ) -> list[WorkSubjectCreate]:
        """
        Prevent duplicate subject relationships.
        """

        subject_ids = [subject.subject_id for subject in value]

        if len(subject_ids) != len(set(subject_ids)):
            raise ValueError(
                "A subject cannot be associated with the same "
                "work more than once."
            )

        return value

    @field_validator("identifiers")
    @classmethod
    def validate_identifiers(
        cls,
        value: list[WorkIdentifierCreate],
    ) -> list[WorkIdentifierCreate]:

        identifiers = [
            (identifier.type, identifier.value.lower().strip())
            for identifier in value
        ]

        if len(identifiers) != len(set(identifiers)):
            raise ValueError(
                "Duplicate Work identifiers are not allowed."
            )

        return value


class WorkCreate(WorkBase):
    """
    Payload used to create a Work.
    """

    pass

class WorkTitleRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: uuid.UUID

    value: str

    language: str | None = None

    title_type: str

    is_preferred: bool = False

    sequence: int | None = None



class WorkIdentifierRead(WorkIdentifierCreate):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: uuid.UUID

class WorkRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: uuid.UUID

    title: str

    titles: list[WorkTitleRead] = []

    types: list[WorkType] = []

    languages: list[str] = []

    agents: list[WorkAgentRead] = []

    subjects: list[WorkSubjectRead] = []

    genres: list[str] = []

    summary: str | None = None

    notes: list[str] = []

    identifiers: list[WorkIdentifierRead] = []

    uri: AnyHttpUrl | None = None

    @field_validator("types", mode="before")
    @classmethod
    def serialize_types(cls, value: Any) -> list[Any]:
        if not value:
            return []

        return [
            item.type if hasattr(item, "type") else item
            for item in value
        ]

    @field_validator("languages", mode="before")
    @classmethod
    def serialize_languages(cls, value: Any) -> list[Any]:
        if not value:
            return []

        return [
            item.language if hasattr(item, "language") else item
            for item in value
        ]

    @field_validator("genres", mode="before")
    @classmethod
    def serialize_genres(cls, value: Any) -> list[Any]:
        if not value:
            return []

        return [
            item.name if hasattr(item, "name") else item
            for item in value
        ]

    @field_validator("notes", mode="before")
    @classmethod
    def serialize_notes(cls, value: Any) -> list[Any]:
        if not value:
            return []

        return [
            item.value if hasattr(item, "value") else item
            for item in value
        ]