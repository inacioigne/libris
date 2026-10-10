from collections.abc import Mapping

from libris.modules.identity.domain.permissions import Permission as P

ROLE_PERMISSIONS: Mapping[str, frozenset[P]] = {
    "libris-reader": frozenset({P.BIBLIOGRAPHIC_READ, P.AUTHORITY_READ}),
    "libris-cataloger": frozenset(
        {
            P.BIBLIOGRAPHIC_READ,
            P.BIBLIOGRAPHIC_CREATE,
            P.BIBLIOGRAPHIC_UPDATE,
            P.AUTHORITY_READ,
            P.METADATA_REVISION_READ,
            P.METADATA_REVISION_CREATE,
        }
    ),
    "libris-authority-manager": frozenset(
        {
            P.BIBLIOGRAPHIC_READ,
            P.AUTHORITY_READ,
            P.AUTHORITY_MANAGE,
        }
    ),
    "libris-admin": frozenset(P),
}


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
