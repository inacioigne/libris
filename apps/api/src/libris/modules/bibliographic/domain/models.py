from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlsplit
from uuid import UUID, uuid4


@dataclass(frozen=True)
class ResourceIdentity:
    internal_id: UUID
    uri: str

    def __post_init__(self) -> None:
        parts = urlsplit(self.uri)
        if parts.scheme not in {"http", "https"} or not parts.netloc:
            raise ValueError("A URI semântica deve ser HTTP(S) absoluta.")
        if parts.query or parts.fragment or parts.username or parts.password:
            raise ValueError("A URI semântica não pode conter credenciais, query ou fragmento.")

    @classmethod
    def create(cls, base_uri: str, internal_id: UUID | None = None) -> "ResourceIdentity":
        parts = urlsplit(base_uri)
        if parts.scheme not in {"http", "https"} or not parts.netloc:
            raise ValueError("A URI base deve ser HTTP(S) absoluta.")
        if parts.query or parts.fragment or parts.username or parts.password:
            raise ValueError("A URI base não pode conter credenciais, query ou fragmento.")
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


class StaleRevisionError(Exception):
    """The supplied revision is no longer current."""
