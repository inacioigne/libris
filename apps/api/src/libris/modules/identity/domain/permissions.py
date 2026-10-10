from enum import StrEnum


class Permission(StrEnum):
    BIBLIOGRAPHIC_READ = "bibliographic:read"
    BIBLIOGRAPHIC_CREATE = "bibliographic:create"
    BIBLIOGRAPHIC_UPDATE = "bibliographic:update"
    BIBLIOGRAPHIC_DELETE = "bibliographic:delete"
    AUTHORITY_READ = "authority:read"
    AUTHORITY_MANAGE = "authority:manage"
    METADATA_REVISION_READ = "metadata_revision:read"
    METADATA_REVISION_CREATE = "metadata_revision:create"
    SYSTEM_ADMIN = "system:admin"
