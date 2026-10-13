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
    EDITORIAL_SUBMIT = "editorial:submit"
    EDITORIAL_APPROVE = "editorial:approve"
    EDITORIAL_RETURN = "editorial:return"
    EDITORIAL_PUBLISH = "editorial:publish"
    EDITORIAL_WITHDRAW = "editorial:withdraw"
    EDITORIAL_REPUBLISH = "editorial:republish"
    EDITORIAL_ARCHIVE = "editorial:archive"
