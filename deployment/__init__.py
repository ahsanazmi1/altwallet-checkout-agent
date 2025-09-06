"""Deployment module for AltWallet Checkout Agent."""

from .config import (
    DeploymentConfig,
    DeploymentMode,
    InlineConfig,
    SidecarConfig,
    get_deployment_mode,
    is_inline_mode,
    is_sidecar_mode,
    load_deployment_config,
)
from .inline.embedded import (
    CircuitBreakerOpenError,
    InlineCheckoutClient,
    SyncInlineCheckoutClient,
    get_inline_client,
    inline_checkout_client,
    process_checkout_inline,
)
from .manager import DeploymentManager, get_deployment_manager, initialize_deployment

__all__ = [
    # Configuration
    "DeploymentConfig",
    "DeploymentMode",
    "SidecarConfig",
    "InlineConfig",
    "load_deployment_config",
    "get_deployment_mode",
    "is_sidecar_mode",
    "is_inline_mode",
    # Deployment management
    "DeploymentManager",
    "get_deployment_manager",
    "initialize_deployment",
    # Inline deployment
    "InlineCheckoutClient",
    "SyncInlineCheckoutClient",
    "get_inline_client",
    "process_checkout_inline",
    "inline_checkout_client",
    "CircuitBreakerOpenError",
]
