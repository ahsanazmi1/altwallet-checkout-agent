"""Deployment configuration management for AltWallet Checkout Agent."""

import os
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class DeploymentMode(Enum):
    """Deployment mode enumeration."""

    SIDECAR = "sidecar"
    INLINE = "inline"


class DeploymentConfig(BaseModel):
    """Base deployment configuration."""

    mode: DeploymentMode = Field(
        default=DeploymentMode.SIDECAR, description="Deployment mode: sidecar or inline"
    )

    # Common configuration
    environment: str = Field(
        default="development", description="Deployment environment"
    )

    log_level: str = Field(default="INFO", description="Logging level")

    api_host: str = Field(default="0.0.0.0", description="API host address")

    api_port: int = Field(default=8000, description="API port number")

    # Health check configuration
    health_check_enabled: bool = Field(
        default=True, description="Enable health check endpoints"
    )

    health_check_interval: int = Field(
        default=30, description="Health check interval in seconds"
    )

    # Performance configuration
    max_workers: int = Field(
        default=4, description="Maximum number of worker processes"
    )

    request_timeout: int = Field(default=30, description="Request timeout in seconds")

    # Security configuration
    cors_origins: list[str] = Field(default=["*"], description="CORS allowed origins")

    api_key_required: bool = Field(
        default=False, description="Require API key authentication"
    )

    # Monitoring configuration
    metrics_enabled: bool = Field(default=True, description="Enable metrics collection")

    tracing_enabled: bool = Field(
        default=True, description="Enable distributed tracing"
    )

    # Mode-specific configuration
    sidecar_config: dict[str, Any] | None = Field(
        default=None, description="Sidecar-specific configuration"
    )

    inline_config: dict[str, Any] | None = Field(
        default=None, description="Inline-specific configuration"
    )


class SidecarConfig(BaseModel):
    """Sidecar deployment specific configuration."""

    container_name: str = Field(
        default="altwallet-checkout-agent", description="Container name"
    )

    image_tag: str = Field(default="latest", description="Docker image tag")

    restart_policy: str = Field(
        default="unless-stopped", description="Container restart policy"
    )

    # Resource limits
    memory_limit: str = Field(default="512Mi", description="Memory limit")

    cpu_limit: str = Field(default="500m", description="CPU limit")

    # Networking
    network_mode: str = Field(default="bridge", description="Docker network mode")

    expose_port: int = Field(default=8000, description="Exposed port")

    # Volume mounts
    config_volume: str | None = Field(
        default=None, description="Configuration volume mount"
    )

    log_volume: str | None = Field(default=None, description="Log volume mount")

    # Environment variables
    env_vars: dict[str, str] = Field(
        default_factory=dict, description="Additional environment variables"
    )


class InlineConfig(BaseModel):
    """Inline deployment specific configuration."""

    # Integration configuration
    merchant_app_name: str = Field(
        default="merchant-app", description="Name of the merchant application"
    )

    integration_method: str = Field(
        default="direct_import",
        description="Integration method: direct_import, http_client, or sdk",
    )

    # Performance tuning
    connection_pool_size: int = Field(
        default=10, description="Connection pool size for HTTP client"
    )

    keep_alive: bool = Field(default=True, description="Enable HTTP keep-alive")

    # Caching configuration
    cache_enabled: bool = Field(default=True, description="Enable response caching")

    cache_ttl: int = Field(default=300, description="Cache TTL in seconds")

    # Error handling
    retry_attempts: int = Field(default=3, description="Number of retry attempts")

    retry_delay: float = Field(default=1.0, description="Retry delay in seconds")

    # Circuit breaker
    circuit_breaker_enabled: bool = Field(
        default=True, description="Enable circuit breaker pattern"
    )

    circuit_breaker_threshold: int = Field(
        default=5, description="Circuit breaker failure threshold"
    )


def load_deployment_config(config_path: str | None = None) -> DeploymentConfig:
    """Load deployment configuration from file or environment variables.

    Args:
        config_path: Path to configuration file (optional)

    Returns:
        DeploymentConfig instance
    """
    config_data = {}

    # First load from environment variables
    env_mappings = {
        "DEPLOYMENT_MODE": "mode",
        "ENVIRONMENT": "environment",
        "LOG_LEVEL": "log_level",
        "API_HOST": "api_host",
        "API_PORT": "api_port",
        "MAX_WORKERS": "max_workers",
        "REQUEST_TIMEOUT": "request_timeout",
        "METRICS_ENABLED": "metrics_enabled",
        "TRACING_ENABLED": "tracing_enabled",
    }

    for env_var, config_key in env_mappings.items():
        if env_var in os.environ:
            value = os.environ[env_var]
            # Type conversion
            if config_key in ["api_port", "max_workers", "request_timeout"]:
                value = int(value)
            elif config_key in ["metrics_enabled", "tracing_enabled"]:
                value = value.lower() in ("true", "1", "yes", "on")
            config_data[config_key] = value

    # Then override with file configuration if provided
    if config_path and os.path.exists(config_path):
        import json

        with open(config_path) as f:
            file_data = json.load(f)
            config_data.update(file_data)

    return DeploymentConfig(**config_data)


def get_deployment_mode() -> DeploymentMode:
    """Get deployment mode from environment or default to sidecar."""
    mode_str = os.getenv("DEPLOYMENT_MODE", "sidecar").lower()
    try:
        return DeploymentMode(mode_str)
    except ValueError:
        return DeploymentMode.SIDECAR


def is_sidecar_mode() -> bool:
    """Check if running in sidecar mode."""
    return get_deployment_mode() == DeploymentMode.SIDECAR


def is_inline_mode() -> bool:
    """Check if running in inline mode."""
    return get_deployment_mode() == DeploymentMode.INLINE
