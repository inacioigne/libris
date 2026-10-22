import re
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import urlsplit
from uuid import UUID, uuid4


@dataclass(frozen=True)
class BibliographicDraft:
    id: UUID
    cataloger_id: UUID

    @classmethod
    def create(cls, cataloger_id: UUID) -> "BibliographicDraft":
        return cls(id=uuid4(), cataloger_id=cataloger_id)


def validate_identity_uri(value: str) -> str:
    """Validate a stored identity/base URI without normalizing or dereferencing it."""
    if not isinstance(value, str) or re.search(r'[\s<>"{}|\\^`\x00-\x20\x7f]', value):
        raise ValueError("A URI semântica contém caracteres inválidos.")
    if re.search(r"%(?![0-9a-fA-F]{2})", value):
        raise ValueError("Escape percentual inválido na URI semântica.")
    parts = urlsplit(value)
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        raise ValueError("A URI semântica deve ser HTTP(S) absoluta com host.")
    if "?" in value or "#" in value or parts.username is not None or parts.password is not None:
        raise ValueError("A URI semântica não pode conter credenciais, query ou fragmento.")
    _ = parts.port
    return value


@dataclass(frozen=True)
class ResourceIdentity:
    internal_id: UUID
    uri: str

    def __post_init__(self) -> None:
        if not isinstance(self.internal_id, UUID):
            raise ValueError("O identificador interno deve ser um UUID.")
        validate_identity_uri(self.uri)

    @classmethod
    def create(cls, base_uri: str, internal_id: UUID | None = None) -> "ResourceIdentity":
        validate_identity_uri(base_uri)
        identifier = internal_id or uuid4()
        return cls(identifier, f"{base_uri.rstrip('/')}/{identifier}")


@dataclass(frozen=True)
class Provenance:
    source: str
    process: str
    reason: str | None = None

    def __post_init__(self) -> None:
        if not self.source.strip() or not self.process.strip():
            raise ValueError("Origem e processo técnico são obrigatórios.")
        if self.reason is not None and (not self.reason.strip() or "\x00" in self.reason):
            raise ValueError("Justificativa fornecida deve ser não vazia.")


@dataclass(frozen=True)
class Revision:
    identity: ResourceIdentity
    number: int
    created_at: datetime
    provenance: Provenance
    profile: str
    actor_id: str | None = None

    def __post_init__(self) -> None:
        if type(self.number) is not int or self.number < 1:
            raise ValueError("A revisão deve ser positiva.")
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("Revisão exige instante com timezone.")
        object.__setattr__(self, "created_at", self.created_at.astimezone(UTC))
        if not self.profile.strip():
            raise ValueError("Revisão exige identificação do perfil.")

    @property
    def concurrency_token(self) -> str:
        """Opaque write token, independent of representation-specific HTTP cache ETags."""
        return revision_token(self.identity.internal_id, self.number)


def revision_token(identifier: UUID, number: int) -> str:
    if number < 1:
        raise ValueError("A revisão deve ser positiva.")
    return f"{identifier}:r{number}"


def require_revision_token(identifier: UUID, number: int, expected: str) -> None:
    if expected != revision_token(identifier, number):
        raise StaleRevisionError("Validador de escrita obsoleto ou incompatível.")


class StaleRevisionError(Exception):
    """The supplied revision is no longer current."""


def validate_history_limit(limit: int) -> None:
    if type(limit) is not int or not 1 <= limit <= 200:
        raise ValueError("Limite deve estar entre 1 e 200.")
