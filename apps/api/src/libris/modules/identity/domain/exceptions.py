class AuthenticationError(Exception):
    """Credentials cannot establish a trusted identity."""


class ProviderUnavailable(AuthenticationError):
    """Trusted provider configuration or keys cannot be retrieved."""


class PermissionDenied(Exception):
    """An execution context cannot authorize the requested operation."""
