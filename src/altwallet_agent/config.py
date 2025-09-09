"""
Configuration management for Orca Checkout Agent.

This module provides backward-compatible configuration management that supports
both the new ORCA_ prefixed environment variables and the legacy AltWallet
variables, with deprecation warnings for the legacy ones.
"""

import os
import warnings
from functools import lru_cache
from typing import Any


class OrcaConfig:
    """Configuration manager with backward compatibility for environment variables."""

    def __init__(self):
        self._deprecation_warnings_issued = set()

    def get_env_var(
        self,
        orca_key: str,
        legacy_key: str | None = None,
        default: Any = None,
        env_type: type = str,
    ) -> Any:
        """
        Get environment variable with ORCA_ prefix, falling back to legacy key.

        Args:
            orca_key: The ORCA_ prefixed environment variable name
            legacy_key: The legacy environment variable name (optional)
            default: Default value if neither variable is set
            env_type: Type to convert the value to (str, int, bool, etc.)

        Returns:
            The environment variable value converted to the specified type
        """
        # Try ORCA_ prefixed variable first
        orca_value = os.getenv(orca_key)
        if orca_value is not None:
            return self._convert_value(orca_value, env_type)

        # Fall back to legacy variable if provided
        if legacy_key:
            legacy_value = os.getenv(legacy_key)
            if legacy_value is not None:
                # Issue deprecation warning (only once per variable)
                warning_key = f"{legacy_key}->{orca_key}"
                if warning_key not in self._deprecation_warnings_issued:
                    warnings.warn(
                        f"Environment variable '{legacy_key}' is deprecated. "
                        f"Please use '{orca_key}' instead. "
                        f"This will be removed in a future version.",
                        DeprecationWarning,
                        stacklevel=2,
                    )
                    self._deprecation_warnings_issued.add(warning_key)

                return self._convert_value(legacy_value, env_type)

        return default

    def _convert_value(self, value: str, env_type: type) -> Any:
        """Convert string value to the specified type."""
        if env_type is bool:
            return value.lower() in ("true", "1", "yes", "on", "enabled")
        elif env_type is int:
            return int(value)
        elif env_type is float:
            return float(value)
        elif env_type is list:
            return [item.strip() for item in value.split(",") if item.strip()]
        else:
            return value

    @property
    def api_endpoint(self) -> str:
        """Get API endpoint URL."""
        return self.get_env_var(
            "ORCA_ENDPOINT", "ALTWALLET_ENDPOINT", "https://api.orca.com"
        )

    @property
    def api_key(self) -> str | None:
        """Get API key."""
        return self.get_env_var("ORCA_API_KEY", "ALTWALLET_API_KEY")

    @property
    def timeout(self) -> int:
        """Get request timeout in milliseconds."""
        return self.get_env_var("ORCA_TIMEOUT", "REQUEST_TIMEOUT", 30000, int)

    @property
    def log_level(self) -> str:
        """Get log level."""
        return self.get_env_var("ORCA_LOG_LEVEL", "LOG_LEVEL", "INFO")

    @property
    def log_format(self) -> str:
        """Get log format."""
        return self.get_env_var("ORCA_LOG_FORMAT", "LOG_FORMAT", "json")

    @property
    def deployment_mode(self) -> str:
        """Get deployment mode."""
        return self.get_env_var("ORCA_DEPLOYMENT_MODE", "DEPLOYMENT_MODE", "sidecar")

    @property
    def environment(self) -> str:
        """Get environment name."""
        return self.get_env_var("ORCA_ENVIRONMENT", "ENVIRONMENT", "development")

    @property
    def database_url(self) -> str | None:
        """Get database URL."""
        return self.get_env_var("ORCA_DATABASE_URL", "DATABASE_URL")

    @property
    def database_pool_size(self) -> int:
        """Get database pool size."""
        return self.get_env_var(
            "ORCA_DATABASE_POOL_SIZE", "DATABASE_POOL_SIZE", 10, int
        )

    @property
    def database_max_overflow(self) -> int:
        """Get database max overflow."""
        return self.get_env_var(
            "ORCA_DATABASE_MAX_OVERFLOW", "DATABASE_MAX_OVERFLOW", 20, int
        )

    @property
    def redis_url(self) -> str | None:
        """Get Redis URL."""
        return self.get_env_var("ORCA_REDIS_URL", "REDIS_URL")

    @property
    def redis_pool_size(self) -> int:
        """Get Redis pool size."""
        return self.get_env_var("ORCA_REDIS_POOL_SIZE", "REDIS_POOL_SIZE", 10, int)

    @property
    def redis_max_connections(self) -> int:
        """Get Redis max connections."""
        return self.get_env_var(
            "ORCA_REDIS_MAX_CONNECTIONS", "REDIS_MAX_CONNECTIONS", 20, int
        )

    @property
    def enable_metrics(self) -> bool:
        """Get metrics enablement flag."""
        return self.get_env_var("ORCA_ENABLE_METRICS", "ENABLE_METRICS", True, bool)

    @property
    def metrics_port(self) -> int:
        """Get metrics port."""
        return self.get_env_var("ORCA_METRICS_PORT", "METRICS_PORT", 9090, int)

    @property
    def health_check_interval(self) -> int:
        """Get health check interval in seconds."""
        return self.get_env_var(
            "ORCA_HEALTH_CHECK_INTERVAL", "HEALTH_CHECK_INTERVAL", 30, int
        )

    @property
    def jwt_secret(self) -> str | None:
        """Get JWT secret."""
        return self.get_env_var("ORCA_JWT_SECRET", "JWT_SECRET")

    @property
    def encryption_key(self) -> str | None:
        """Get encryption key."""
        return self.get_env_var("ORCA_ENCRYPTION_KEY", "ENCRYPTION_KEY")

    @property
    def cors_origins(self) -> list:
        """Get CORS origins."""
        return self.get_env_var("ORCA_CORS_ORIGINS", "CORS_ORIGINS", [], list)

    @property
    def enable_analytics(self) -> bool:
        """Get analytics enablement flag."""
        return self.get_env_var("ORCA_ENABLE_ANALYTICS", "ENABLE_ANALYTICS", True, bool)

    @property
    def enable_webhooks(self) -> bool:
        """Get webhooks enablement flag."""
        return self.get_env_var("ORCA_ENABLE_WEBHOOKS", "ENABLE_WEBHOOKS", True, bool)

    @property
    def enable_caching(self) -> bool:
        """Get caching enablement flag."""
        return self.get_env_var("ORCA_ENABLE_CACHING", "ENABLE_CACHING", True, bool)

    @property
    def cache_ttl(self) -> int:
        """Get cache TTL in seconds."""
        return self.get_env_var("ORCA_CACHE_TTL", "CACHE_TTL", 300, int)

    @property
    def max_workers(self) -> int:
        """Get maximum number of workers."""
        return self.get_env_var("ORCA_MAX_WORKERS", "MAX_WORKERS", 4, int)

    @property
    def request_timeout(self) -> int:
        """Get request timeout in seconds."""
        return self.get_env_var("ORCA_REQUEST_TIMEOUT", "REQUEST_TIMEOUT", 30, int)

    @property
    def rate_limit(self) -> int:
        """Get rate limit per minute."""
        return self.get_env_var("ORCA_RATE_LIMIT", "RATE_LIMIT", 1000, int)

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "api_endpoint": self.api_endpoint,
            "api_key": self.api_key,
            "timeout": self.timeout,
            "log_level": self.log_level,
            "log_format": self.log_format,
            "deployment_mode": self.deployment_mode,
            "environment": self.environment,
            "database_url": self.database_url,
            "database_pool_size": self.database_pool_size,
            "database_max_overflow": self.database_max_overflow,
            "redis_url": self.redis_url,
            "redis_pool_size": self.redis_pool_size,
            "redis_max_connections": self.redis_max_connections,
            "enable_metrics": self.enable_metrics,
            "metrics_port": self.metrics_port,
            "health_check_interval": self.health_check_interval,
            "jwt_secret": self.jwt_secret,
            "encryption_key": self.encryption_key,
            "cors_origins": self.cors_origins,
            "enable_analytics": self.enable_analytics,
            "enable_webhooks": self.enable_webhooks,
            "enable_caching": self.enable_caching,
            "cache_ttl": self.cache_ttl,
            "max_workers": self.max_workers,
            "request_timeout": self.request_timeout,
            "rate_limit": self.rate_limit,
        }


# Global configuration instance
@lru_cache
def get_config() -> OrcaConfig:
    """Get the global configuration instance."""
    return OrcaConfig()


# Convenience functions for backward compatibility
def get_api_endpoint() -> str:
    """Get API endpoint URL."""
    return get_config().api_endpoint


def get_api_key() -> str | None:
    """Get API key."""
    return get_config().api_key


def get_timeout() -> int:
    """Get request timeout in milliseconds."""
    return get_config().timeout


def get_log_level() -> str:
    """Get log level."""
    return get_config().log_level


def get_deployment_mode() -> str:
    """Get deployment mode."""
    return get_config().deployment_mode


def get_environment() -> str:
    """Get environment name."""
    return get_config().environment
