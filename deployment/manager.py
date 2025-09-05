"""Deployment manager for handling different deployment modes."""

import os
from typing import Any, Dict, Optional, Union

import structlog
from pydantic import BaseModel

from .config import (
    DeploymentConfig,
    DeploymentMode,
    SidecarConfig,
    InlineConfig,
    get_deployment_mode,
    is_sidecar_mode,
    is_inline_mode,
)
from .inline.embedded import InlineCheckoutClient, SyncInlineCheckoutClient


class DeploymentManager:
    """Manages deployment mode selection and initialization."""
    
    def __init__(self, config: Optional[DeploymentConfig] = None):
        """Initialize deployment manager.
        
        Args:
            config: Deployment configuration
        """
        self.config = config or DeploymentConfig()
        self.logger = structlog.get_logger(__name__)
        self._mode = self._determine_deployment_mode()
        self._initialized = False
        
        self.logger.info(
            "Deployment manager initialized",
            mode=self._mode.value,
            environment=self.config.environment
        )
    
    def _determine_deployment_mode(self) -> DeploymentMode:
        """Determine deployment mode from configuration and environment."""
        # Check environment variable first
        env_mode = os.getenv('DEPLOYMENT_MODE')
        if env_mode:
            try:
                return DeploymentMode(env_mode.lower())
            except ValueError:
                self.logger.warning(
                    "Invalid DEPLOYMENT_MODE environment variable",
                    value=env_mode,
                    defaulting_to=self.config.mode.value
                )
        
        # Use configuration default
        return self.config.mode
    
    @property
    def mode(self) -> DeploymentMode:
        """Get current deployment mode."""
        return self._mode
    
    @property
    def is_sidecar(self) -> bool:
        """Check if running in sidecar mode."""
        return self._mode == DeploymentMode.SIDECAR
    
    @property
    def is_inline(self) -> bool:
        """Check if running in inline mode."""
        return self._mode == DeploymentMode.INLINE
    
    def get_mode_config(self) -> Union[SidecarConfig, InlineConfig]:
        """Get mode-specific configuration.
        
        Returns:
            Mode-specific configuration object
            
        Raises:
            ValueError: If mode is not supported
        """
        if self.is_sidecar:
            if self.config.sidecar_config:
                return SidecarConfig(**self.config.sidecar_config)
            return SidecarConfig()
        elif self.is_inline:
            if self.config.inline_config:
                return InlineConfig(**self.config.inline_config)
            return InlineConfig()
        else:
            raise ValueError(f"Unsupported deployment mode: {self._mode}")
    
    def get_startup_message(self) -> str:
        """Get startup message for the deployment mode."""
        if self.is_sidecar:
            return (
                "🚀 AltWallet Checkout Agent starting in SIDECAR mode\n"
                "   - Running as containerized service\n"
                "   - Accessible via HTTP API\n"
                "   - Health checks enabled\n"
                f"   - Environment: {self.config.environment}"
            )
        elif self.is_inline:
            return (
                "🔧 AltWallet Checkout Agent starting in INLINE mode\n"
                "   - Embedded in merchant application\n"
                "   - Direct function calls\n"
                "   - Optimized for performance\n"
                f"   - Environment: {self.config.environment}"
            )
        else:
            return f"❓ AltWallet Checkout Agent starting in {self._mode.value} mode"
    
    def get_health_check_config(self) -> Dict[str, Any]:
        """Get health check configuration for the deployment mode."""
        base_config = {
            "enabled": self.config.health_check_enabled,
            "interval": self.config.health_check_interval,
        }
        
        if self.is_sidecar:
            base_config.update({
                "endpoint": "/health",
                "port": self.config.api_port,
                "host": self.config.api_host,
            })
        elif self.is_inline:
            base_config.update({
                "method": "function_call",
                "timeout": 5,
            })
        
        return base_config
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration for the deployment mode."""
        config = {
            "level": self.config.log_level,
            "structured": True,
            "format": "json",
        }
        
        if self.is_sidecar:
            config.update({
                "destinations": ["console", "file"],
                "file_path": "/app/logs/altwallet.log",
            })
        elif self.is_inline:
            config.update({
                "destinations": ["console"],
                "component": "inline",
            })
        
        return config
    
    def get_metrics_config(self) -> Dict[str, Any]:
        """Get metrics configuration for the deployment mode."""
        config = {
            "enabled": self.config.metrics_enabled,
            "tracing_enabled": self.config.tracing_enabled,
        }
        
        if self.is_sidecar:
            config.update({
                "endpoint": "/metrics",
                "port": 9090,
                "path": "/metrics",
            })
        elif self.is_inline:
            config.update({
                "method": "internal",
                "export_interval": 60,
            })
        
        return config
    
    def create_inline_client(self) -> Union[InlineCheckoutClient, SyncInlineCheckoutClient]:
        """Create inline client for inline deployment mode.
        
        Returns:
            Inline checkout client
            
        Raises:
            ValueError: If not in inline mode
        """
        if not self.is_inline:
            raise ValueError("Inline client can only be created in inline mode")
        
        inline_config = self.get_mode_config()
        return InlineCheckoutClient(inline_config)
    
    def create_sync_inline_client(self) -> SyncInlineCheckoutClient:
        """Create synchronous inline client for inline deployment mode.
        
        Returns:
            Synchronous inline checkout client
            
        Raises:
            ValueError: If not in inline mode
        """
        if not self.is_inline:
            raise ValueError("Sync inline client can only be created in inline mode")
        
        inline_config = self.get_mode_config()
        return SyncInlineCheckoutClient(inline_config)
    
    def get_deployment_info(self) -> Dict[str, Any]:
        """Get comprehensive deployment information."""
        return {
            "mode": self._mode.value,
            "environment": self.config.environment,
            "initialized": self._initialized,
            "config": {
                "api_host": self.config.api_host,
                "api_port": self.config.api_port,
                "log_level": self.config.log_level,
                "max_workers": self.config.max_workers,
                "request_timeout": self.config.request_timeout,
                "health_check_enabled": self.config.health_check_enabled,
                "metrics_enabled": self.config.metrics_enabled,
                "tracing_enabled": self.config.tracing_enabled,
            },
            "mode_config": self.get_mode_config().dict(),
            "health_check": self.get_health_check_config(),
            "logging": self.get_logging_config(),
            "metrics": self.get_metrics_config(),
        }
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate deployment configuration.
        
        Returns:
            Validation results
        """
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
        }
        
        # Validate mode-specific configuration
        try:
            mode_config = self.get_mode_config()
            validation_results["mode_config_valid"] = True
        except Exception as e:
            validation_results["valid"] = False
            validation_results["errors"].append(f"Mode config validation failed: {e}")
            validation_results["mode_config_valid"] = False
        
        # Validate port configuration
        if self.config.api_port < 1 or self.config.api_port > 65535:
            validation_results["valid"] = False
            validation_results["errors"].append(f"Invalid API port: {self.config.api_port}")
        
        # Validate worker configuration
        if self.config.max_workers < 1:
            validation_results["warnings"].append(f"Low max_workers value: {self.config.max_workers}")
        
        # Validate timeout configuration
        if self.config.request_timeout < 1:
            validation_results["warnings"].append(f"Low request_timeout value: {self.config.request_timeout}")
        
        # Mode-specific validations
        if self.is_sidecar:
            sidecar_config = self.get_mode_config()
            if not sidecar_config.container_name:
                validation_results["warnings"].append("Container name not specified")
        
        elif self.is_inline:
            inline_config = self.get_mode_config()
            if inline_config.retry_attempts < 0:
                validation_results["valid"] = False
                validation_results["errors"].append("Invalid retry_attempts value")
        
        return validation_results


# Global deployment manager instance
_deployment_manager: Optional[DeploymentManager] = None


def get_deployment_manager() -> DeploymentManager:
    """Get or create the global deployment manager instance."""
    global _deployment_manager
    
    if _deployment_manager is None:
        _deployment_manager = DeploymentManager()
    
    return _deployment_manager


def initialize_deployment(config: Optional[DeploymentConfig] = None) -> DeploymentManager:
    """Initialize deployment with configuration.
    
    Args:
        config: Deployment configuration
        
    Returns:
        Initialized deployment manager
    """
    global _deployment_manager
    
    _deployment_manager = DeploymentManager(config)
    _deployment_manager._initialized = True
    
    return _deployment_manager
