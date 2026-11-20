from functools import lru_cache
from importlib.resources import files

from pydantic import BaseModel, ConfigDict, HttpUrl


class VocabularyNotFoundError(LookupError):
    """Raised when a controlled vocabulary is not available locally."""


class VocabularyTerm(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    uri: HttpUrl
    code: str
    label: str


class Vocabulary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    vocabulary: str
    version: str
    terms: tuple[VocabularyTerm, ...]


_VOCABULARY_FILES = {
    "loc-languages": "loc-languages.v1.json",
}


@lru_cache
def get_vocabulary(name: str) -> Vocabulary:
    """Load and validate a versioned controlled vocabulary bundled with the API."""
    try:
        filename = _VOCABULARY_FILES[name]
    except KeyError as exc:
        raise VocabularyNotFoundError(name) from exc

    resource = files("app.modules.bibliograph.resources.vocabularies").joinpath(
        filename
    )
    return Vocabulary.model_validate_json(resource.read_text(encoding="utf-8"))
