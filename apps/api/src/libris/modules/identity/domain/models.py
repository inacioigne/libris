import hashlib
import json
from dataclasses import dataclass

from libris.modules.identity.domain.permissions import Permission


def actor_identifier(issuer: str, subject: str) -> str:
    pair = json.dumps([issuer, subject], ensure_ascii=False, separators=(",", ":"))
    return "oidc:sha256:" + hashlib.sha256(pair.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class AuthenticatedActor:
    actor_id: str
    issuer: str
    subject: str
    roles: frozenset[str]
    permissions: frozenset[Permission]
