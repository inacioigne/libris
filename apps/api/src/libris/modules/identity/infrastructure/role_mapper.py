from collections.abc import Mapping
from types import MappingProxyType

from libris.modules.identity.domain.permissions import Permission as P

ROLE_PERMISSIONS: Mapping[str, frozenset[P]] = MappingProxyType(
    {
        "libris-reader": frozenset({P.BIBLIOGRAPHIC_READ, P.AUTHORITY_READ}),
        "libris-cataloger": frozenset(
            {
                P.BIBLIOGRAPHIC_READ,
                P.BIBLIOGRAPHIC_CREATE,
                P.BIBLIOGRAPHIC_UPDATE,
                P.AUTHORITY_READ,
                P.METADATA_REVISION_READ,
                P.METADATA_REVISION_CREATE,
                P.EDITORIAL_SUBMIT,
            }
        ),
        "libris-authority-manager": frozenset(
            {
                P.BIBLIOGRAPHIC_READ,
                P.AUTHORITY_READ,
                P.AUTHORITY_MANAGE,
            }
        ),
        "libris-reviewer": frozenset(
            {
                P.BIBLIOGRAPHIC_READ,
                P.AUTHORITY_READ,
                P.METADATA_REVISION_READ,
                P.METADATA_AUDIT_READ,
                P.EDITORIAL_APPROVE,
                P.EDITORIAL_RETURN,
            }
        ),
        "libris-publisher": frozenset(
            {
                P.BIBLIOGRAPHIC_READ,
                P.AUTHORITY_READ,
                P.METADATA_REVISION_READ,
                P.METADATA_AUDIT_READ,
                P.EDITORIAL_PUBLISH,
                P.EDITORIAL_WITHDRAW,
                P.EDITORIAL_REPUBLISH,
                P.EDITORIAL_ARCHIVE,
            }
        ),
        "libris-admin": frozenset(
            {
                P.BIBLIOGRAPHIC_READ,
                P.BIBLIOGRAPHIC_CREATE,
                P.BIBLIOGRAPHIC_UPDATE,
                P.BIBLIOGRAPHIC_DELETE,
                P.AUTHORITY_READ,
                P.AUTHORITY_MANAGE,
                P.METADATA_AUDIT_READ,
                P.METADATA_REVISION_READ,
                P.METADATA_REVISION_CREATE,
                P.SYSTEM_ADMIN,
                P.EDITORIAL_SUBMIT,
                P.EDITORIAL_APPROVE,
                P.EDITORIAL_RETURN,
                P.EDITORIAL_PUBLISH,
                P.EDITORIAL_WITHDRAW,
                P.EDITORIAL_REPUBLISH,
                P.EDITORIAL_ARCHIVE,
            }
        ),
    }
)


def extract_roles(claims: Mapping[str, object], source: str, client: str) -> frozenset[str]:
    container = claims.get("realm_access")
    if source == "client":
        resources = claims.get("resource_access")
        container = resources.get(client) if isinstance(resources, dict) else None
    roles = container.get("roles") if isinstance(container, dict) else None
    if not isinstance(roles, list) or not all(isinstance(role, str) for role in roles):
        return frozenset()
    return frozenset(roles)


def map_permissions(roles: frozenset[str]) -> frozenset[P]:
    return frozenset(permission for role in roles for permission in ROLE_PERMISSIONS.get(role, ()))
