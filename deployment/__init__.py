"""Deployment module for AltWallet Checkout Agent."""

from .config import (
    DeploymentConfig,
    DeploymentMode,
    SidecarConfig,
    InlineConfig,
    load_deployment_config,
    get_deployment_mode,
    is_sidecar_mode,
    is_inline_mode,
)

from .inline.embedded import (
    InlineCheckoutClient,
    SyncInlineCheckoutClient,
    get_inline_client,
    process_checkout_inline,
    inline_checkout_client,
    CircuitBreakerOpenError,
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
