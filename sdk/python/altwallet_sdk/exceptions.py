"""Custom exceptions for the AltWallet Python SDK."""

from typing import Any


class AltWalletError(Exception):
    """Base exception for all AltWallet SDK errors."""

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        request_id: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.request_id = request_id
        self.details = details or {}

    def __str__(self) -> str:
        parts = [self.message]
        if self.error_code:
            parts.append(f" (Code: {self.error_code})")
        if self.request_id:
            parts.append(f" (Request ID: {self.request_id})")
        return " ".join(parts)


class ConfigurationError(AltWalletError):
    """Raised when SDK configuration is invalid."""

    pass


class NetworkError(AltWalletError):
    """Raised when network communication fails."""

    pass


class AuthenticationError(AltWalletError):
    """Raised when authentication fails."""

    pass


class ValidationError(AltWalletError):
    """Raised when request validation fails."""

    pass


class RateLimitError(AltWalletError):
    """Raised when rate limit is exceeded."""

    pass


class APIError(AltWalletError):
    """Raised when the API returns an error response."""

    def __init__(
        self,
        message: str,
        status_code: int,
        error_code: str | None = None,
        request_id: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, error_code, request_id, details)
        self.status_code = status_code

    def __str__(self) -> str:
        return f"{super().__str__()} (Status: {self.status_code})"
