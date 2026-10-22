from typing import Literal


class AuthenticationError(Exception):
    """Credentials cannot establish a trusted identity."""

    def __init__(
        self, *, reason: Literal["invalid_token", "client_not_allowed"] = "invalid_token"
    ) -> None:
        self.reason = reason
        super().__init__()


class ProviderUnavailable(AuthenticationError):
    """Trusted provider configuration or keys cannot be retrieved."""


class PermissionDenied(Exception):
    """An execution context cannot authorize the requested operation."""
