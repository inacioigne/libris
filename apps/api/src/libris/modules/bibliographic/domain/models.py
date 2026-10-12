import re
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlsplit
from uuid import UUID, uuid4


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

    def __post_init__(self) -> None:
        if not self.source.strip() or not self.process.strip():
            raise ValueError("Origem e processo técnico são obrigatórios.")


@dataclass(frozen=True)
class Revision:
    identity: ResourceIdentity
    number: int
    created_at: datetime
    provenance: Provenance
    profile: str
    actor_id: str | None = None

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
