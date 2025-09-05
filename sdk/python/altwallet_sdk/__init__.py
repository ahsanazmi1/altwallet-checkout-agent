"""AltWallet Checkout Agent Python SDK.

This SDK provides a Python client for integrating with the AltWallet Checkout Agent
to get intelligent card recommendations and transaction scoring.
"""

from .client import AltWalletClient
from .exceptions import (
    AltWalletError,
    AuthenticationError,
    ConfigurationError,
    NetworkError,
    RateLimitError,
    ValidationError,
)
from .models import (
    Cart,
    Context,
    Customer,
    DecisionRequest,
    DecisionResponse,
    ErrorResponse,
    QuoteRequest,
    QuoteResponse,
    Recommendation,
    SDKConfig,
)

__version__ = "1.0.0"
__author__ = "AltWallet Team"

__all__ = [
    # Client
    "AltWalletClient",
    # Models
    "SDKConfig",
    "Cart",
    "Customer",
    "Context",
    "QuoteRequest",
    "QuoteResponse",
    "DecisionRequest",
    "DecisionResponse",
    "Recommendation",
    "ErrorResponse",
    # Exceptions
    "AltWalletError",
    "ConfigurationError",
    "NetworkError",
    "AuthenticationError",
    "ValidationError",
    "RateLimitError",
]
