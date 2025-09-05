"""
Tests for deployment profiles and configuration management.

These tests ensure that both sidecar and inline deployment modes
work correctly with proper configuration and error handling.
"""

import pytest
import json
import os
import tempfile
import time
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

from deployment import (
    DeploymentConfig,
    DeploymentMode,
    SidecarConfig,
    InlineConfig,
    load_deployment_config,
    get_deployment_mode,
    is_sidecar_mode,
    is_inline_mode,
    DeploymentManager,
    get_deployment_manager,
    initialize_deployment,
)
from deployment.inline.embedded import (
    InlineCheckoutClient,
    SyncInlineCheckoutClient,
    get_inline_client,
    process_checkout_inline,
    inline_checkout_client,
    CircuitBreakerOpenError,
)


class TestDeploymentConfig:
    """Test deployment configuration management."""
    
    def test_deployment_config_defaults(self):
        """Test default deployment configuration values."""
        config = DeploymentConfig()
        
        assert config.mode == DeploymentMode.SIDECAR
        assert config.environment == "development"
        assert config.log_level == "INFO"
        assert config.api_host == "0.0.0.0"
        assert config.api_port == 8000
        assert config.max_workers == 4
        assert config.request_timeout == 30
        assert config.health_check_enabled is True
        assert config.metrics_enabled is True
        assert config.tracing_enabled is True
    
    def test_deployment_config_custom_values(self):
        """Test custom deployment configuration values."""
        config = DeploymentConfig(
            mode=DeploymentMode.INLINE,
            environment="production",
            log_level="DEBUG",
            api_port=9000,
            max_workers=8
        )
        
        assert config.mode == DeploymentMode.INLINE
        assert config.environment == "production"
        assert config.log_level == "DEBUG"
        assert config.api_port == 9000
        assert config.max_workers == 8
    
    def test_sidecar_config_defaults(self):
        """Test default sidecar configuration values."""
        config = SidecarConfig()
        
        assert config.container_name == "altwallet-checkout-agent"
        assert config.image_tag == "latest"
        assert config.restart_policy == "unless-stopped"
        assert config.memory_limit == "512Mi"
        assert config.cpu_limit == "500m"
        assert config.network_mode == "bridge"
        assert config.expose_port == 8000
    
    def test_inline_config_defaults(self):
        """Test default inline configuration values."""
        config = InlineConfig()
        
        assert config.merchant_app_name == "merchant-app"
        assert config.integration_method == "direct_import"
        assert config.connection_pool_size == 10
        assert config.keep_alive is True
        assert config.cache_enabled is True
        assert config.cache_ttl == 300
        assert config.retry_attempts == 3
        assert config.retry_delay == 1.0
        assert config.circuit_breaker_enabled is True
        assert config.circuit_breaker_threshold == 5


class TestDeploymentModeSelection:
    """Test deployment mode selection and environment variable handling."""
    
    def test_get_deployment_mode_default(self):
        """Test default deployment mode when no environment variable is set."""
        with patch.dict(os.environ, {}, clear=True):
            mode = get_deployment_mode()
            assert mode == DeploymentMode.SIDECAR
    
    def test_get_deployment_mode_sidecar(self):
        """Test sidecar deployment mode selection."""
        with patch.dict(os.environ, {"DEPLOYMENT_MODE": "sidecar"}):
            mode = get_deployment_mode()
            assert mode == DeploymentMode.SIDECAR
    
    def test_get_deployment_mode_inline(self):
        """Test inline deployment mode selection."""
        with patch.dict(os.environ, {"DEPLOYMENT_MODE": "inline"}):
            mode = get_deployment_mode()
            assert mode == DeploymentMode.INLINE
    
    def test_get_deployment_mode_invalid(self):
        """Test invalid deployment mode falls back to default."""
        with patch.dict(os.environ, {"DEPLOYMENT_MODE": "invalid"}):
            mode = get_deployment_mode()
            assert mode == DeploymentMode.SIDECAR
    
    def test_is_sidecar_mode(self):
        """Test sidecar mode detection."""
        with patch.dict(os.environ, {"DEPLOYMENT_MODE": "sidecar"}):
            assert is_sidecar_mode() is True
            assert is_inline_mode() is False
    
    def test_is_inline_mode(self):
        """Test inline mode detection."""
        with patch.dict(os.environ, {"DEPLOYMENT_MODE": "inline"}):
            assert is_inline_mode() is True
            assert is_sidecar_mode() is False


class TestConfigurationLoading:
    """Test configuration loading from files and environment variables."""
    
    def test_load_deployment_config_from_file(self):
        """Test loading configuration from JSON file."""
        config_data = {
            "mode": "inline",
            "environment": "production",
            "log_level": "DEBUG",
            "api_port": 9000,
            "inline_config": {
                "merchant_app_name": "test-app",
                "cache_enabled": False
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            config = load_deployment_config(config_path)
            
            assert config.mode == DeploymentMode.INLINE
            assert config.environment == "production"
            assert config.log_level == "DEBUG"
            assert config.api_port == 9000
            assert config.inline_config is not None
            assert config.inline_config["merchant_app_name"] == "test-app"
            assert config.inline_config["cache_enabled"] is False
        finally:
            os.unlink(config_path)
    
    def test_load_deployment_config_from_env(self):
        """Test loading configuration from environment variables."""
        env_vars = {
            "DEPLOYMENT_MODE": "inline",
            "ENVIRONMENT": "staging",
            "LOG_LEVEL": "WARNING",
            "API_PORT": "9000",
            "MAX_WORKERS": "8",
            "METRICS_ENABLED": "false"
        }
        
        with patch.dict(os.environ, env_vars):
            config = load_deployment_config()
            
            assert config.mode == DeploymentMode.INLINE
            assert config.environment == "staging"
            assert config.log_level == "WARNING"
            assert config.api_port == 9000
            assert config.max_workers == 8
            assert config.metrics_enabled is False
    
    def test_load_deployment_config_file_override_env(self):
        """Test that file configuration overrides environment variables."""
        config_data = {
            "mode": "sidecar",
            "environment": "production",
            "api_port": 8000
        }
        
        env_vars = {
            "DEPLOYMENT_MODE": "inline",
            "ENVIRONMENT": "development",
            "API_PORT": "9000"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            with patch.dict(os.environ, env_vars):
                config = load_deployment_config(config_path)
                
                # File values should take precedence
                assert config.mode == DeploymentMode.SIDECAR
                assert config.environment == "production"
                assert config.api_port == 8000
        finally:
            os.unlink(config_path)


class TestDeploymentManager:
    """Test deployment manager functionality."""
    
    def test_deployment_manager_initialization(self):
        """Test deployment manager initialization."""
        manager = DeploymentManager()
        
        assert manager.mode == DeploymentMode.SIDECAR
        assert manager.is_sidecar is True
        assert manager.is_inline is False
        assert manager._initialized is False
    
    def test_deployment_manager_custom_config(self):
        """Test deployment manager with custom configuration."""
        config = DeploymentConfig(
            mode=DeploymentMode.INLINE,
            environment="production"
        )
        
        manager = DeploymentManager(config)
        
        assert manager.mode == DeploymentMode.INLINE
        assert manager.is_inline is True
        assert manager.is_sidecar is False
    
    def test_deployment_manager_env_override(self):
        """Test that environment variables override configuration."""
        config = DeploymentConfig(mode=DeploymentMode.SIDECAR)
        
        with patch.dict(os.environ, {"DEPLOYMENT_MODE": "inline"}):
            manager = DeploymentManager(config)
            
            assert manager.mode == DeploymentMode.INLINE
    
    def test_get_mode_config_sidecar(self):
        """Test getting sidecar configuration."""
        manager = DeploymentManager()
        sidecar_config = manager.get_mode_config()
        
        assert isinstance(sidecar_config, SidecarConfig)
        assert sidecar_config.container_name == "altwallet-checkout-agent"
    
    def test_get_mode_config_inline(self):
        """Test getting inline configuration."""
        config = DeploymentConfig(mode=DeploymentMode.INLINE)
        manager = DeploymentManager(config)
        inline_config = manager.get_mode_config()
        
        assert isinstance(inline_config, InlineConfig)
        assert inline_config.merchant_app_name == "merchant-app"
    
    def test_get_startup_message_sidecar(self):
        """Test sidecar startup message."""
        manager = DeploymentManager()
        message = manager.get_startup_message()
        
        assert "SIDECAR mode" in message
        assert "containerized service" in message
        assert "HTTP API" in message
    
    def test_get_startup_message_inline(self):
        """Test inline startup message."""
        config = DeploymentConfig(mode=DeploymentMode.INLINE)
        manager = DeploymentManager(config)
        message = manager.get_startup_message()
        
        assert "INLINE mode" in message
        assert "Embedded in merchant application" in message
        assert "Direct function calls" in message
    
    def test_get_health_check_config_sidecar(self):
        """Test sidecar health check configuration."""
        manager = DeploymentManager()
        health_config = manager.get_health_check_config()
        
        assert health_config["enabled"] is True
        assert health_config["endpoint"] == "/health"
        assert health_config["port"] == 8000
    
    def test_get_health_check_config_inline(self):
        """Test inline health check configuration."""
        config = DeploymentConfig(mode=DeploymentMode.INLINE)
        manager = DeploymentManager(config)
        health_config = manager.get_health_check_config()
        
        assert health_config["enabled"] is True
        assert health_config["method"] == "function_call"
        assert health_config["timeout"] == 5
    
    def test_get_logging_config_sidecar(self):
        """Test sidecar logging configuration."""
        manager = DeploymentManager()
        logging_config = manager.get_logging_config()
        
        assert logging_config["level"] == "INFO"
        assert logging_config["structured"] is True
        assert "file" in logging_config["destinations"]
    
    def test_get_logging_config_inline(self):
        """Test inline logging configuration."""
        config = DeploymentConfig(mode=DeploymentMode.INLINE)
        manager = DeploymentManager(config)
        logging_config = manager.get_logging_config()
        
        assert logging_config["level"] == "INFO"
        assert logging_config["structured"] is True
        assert logging_config["destinations"] == ["console"]
    
    def test_get_metrics_config_sidecar(self):
        """Test sidecar metrics configuration."""
        manager = DeploymentManager()
        metrics_config = manager.get_metrics_config()
        
        assert metrics_config["enabled"] is True
        assert metrics_config["endpoint"] == "/metrics"
        assert metrics_config["port"] == 9090
    
    def test_get_metrics_config_inline(self):
        """Test inline metrics configuration."""
        config = DeploymentConfig(mode=DeploymentMode.INLINE)
        manager = DeploymentManager(config)
        metrics_config = manager.get_metrics_config()
        
        assert metrics_config["enabled"] is True
        assert metrics_config["method"] == "internal"
        assert metrics_config["export_interval"] == 60
    
    def test_create_inline_client_sidecar_mode(self):
        """Test that inline client creation fails in sidecar mode."""
        manager = DeploymentManager()
        
        with pytest.raises(ValueError, match="Inline client can only be created in inline mode"):
            manager.create_inline_client()
    
    def test_create_inline_client_inline_mode(self):
        """Test inline client creation in inline mode."""
        config = DeploymentConfig(mode=DeploymentMode.INLINE)
        manager = DeploymentManager(config)
        
        client = manager.create_inline_client()
        assert isinstance(client, InlineCheckoutClient)
    
    def test_create_sync_inline_client_sidecar_mode(self):
        """Test that sync inline client creation fails in sidecar mode."""
        manager = DeploymentManager()
        
        with pytest.raises(ValueError, match="Sync inline client can only be created in inline mode"):
            manager.create_sync_inline_client()
    
    def test_create_sync_inline_client_inline_mode(self):
        """Test sync inline client creation in inline mode."""
        config = DeploymentConfig(mode=DeploymentMode.INLINE)
        manager = DeploymentManager(config)
        
        client = manager.create_sync_inline_client()
        assert isinstance(client, SyncInlineCheckoutClient)
    
    def test_get_deployment_info(self):
        """Test getting comprehensive deployment information."""
        manager = DeploymentManager()
        info = manager.get_deployment_info()
        
        assert "mode" in info
        assert "environment" in info
        assert "initialized" in info
        assert "config" in info
        assert "mode_config" in info
        assert "health_check" in info
        assert "logging" in info
        assert "metrics" in info
    
    def test_validate_configuration_valid(self):
        """Test configuration validation with valid config."""
        manager = DeploymentManager()
        validation = manager.validate_configuration()
        
        assert validation["valid"] is True
        assert len(validation["errors"]) == 0
        assert validation["mode_config_valid"] is True
    
    def test_validate_configuration_invalid_port(self):
        """Test configuration validation with invalid port."""
        config = DeploymentConfig(api_port=70000)  # Invalid port
        manager = DeploymentManager(config)
        validation = manager.validate_configuration()
        
        assert validation["valid"] is False
        assert len(validation["errors"]) > 0
        assert any("Invalid API port" in error for error in validation["errors"])
    
    def test_validate_configuration_warnings(self):
        """Test configuration validation with warnings."""
        config = DeploymentConfig(max_workers=0, request_timeout=0)
        manager = DeploymentManager(config)
        validation = manager.validate_configuration()
        
        assert validation["valid"] is True
        assert len(validation["warnings"]) > 0


class TestGlobalDeploymentManager:
    """Test global deployment manager functionality."""
    
    def test_get_deployment_manager_singleton(self):
        """Test that get_deployment_manager returns singleton instance."""
        manager1 = get_deployment_manager()
        manager2 = get_deployment_manager()
        
        assert manager1 is manager2
    
    def test_initialize_deployment(self):
        """Test deployment initialization."""
        config = DeploymentConfig(mode=DeploymentMode.INLINE)
        manager = initialize_deployment(config)
        
        assert manager.mode == DeploymentMode.INLINE
        assert manager._initialized is True


class TestInlineCheckoutClient:
    """Test inline checkout client functionality."""
    
    @pytest.fixture
    def mock_agent(self):
        """Mock checkout agent for testing."""
        agent = AsyncMock()
        agent.process_checkout = AsyncMock()
        agent.process_with_context = AsyncMock()
        return agent
    
    @pytest.fixture
    def inline_client(self):
        """Create inline checkout client for testing."""
        return InlineCheckoutClient()
    
    @pytest.mark.asyncio
    async def test_inline_client_initialization(self, inline_client):
        """Test inline client initialization."""
        with patch('deployment.inline.embedded.CheckoutAgent') as mock_agent_class:
            mock_agent = AsyncMock()
            mock_agent_class.return_value = mock_agent
            
            await inline_client.initialize()
            
            assert inline_client._initialized is True
            assert inline_client._agent is not None
    
    @pytest.mark.asyncio
    async def test_process_checkout_success(self, inline_client, mock_agent):
        """Test successful checkout processing."""
        inline_client._agent = mock_agent
        inline_client._initialized = True
        
        # Mock response
        mock_response = Mock()
        mock_response.transaction_id = "test-123"
        mock_response.recommendations = [
            Mock(card_name="Test Card", rank=1, p_approval=0.9, expected_rewards=0.05, utility=0.8)
        ]
        mock_agent.process_checkout.return_value = mock_response
        
        request = Mock()
        response = await inline_client.process_checkout(request)
        
        assert response.transaction_id == "test-123"
        assert inline_client._request_count == 1
        assert inline_client._error_count == 0
    
    @pytest.mark.asyncio
    async def test_process_checkout_circuit_breaker_open(self, inline_client):
        """Test checkout processing with circuit breaker open."""
        inline_client._initialized = True
        inline_client._agent = AsyncMock()  # Set an async mock agent
        inline_client._circuit_breaker_state = "open"
        inline_client._circuit_breaker_last_failure = time.time()  # Recent failure
        
        request = Mock()
        
        with pytest.raises(CircuitBreakerOpenError):
            await inline_client.process_checkout(request)
    
    @pytest.mark.asyncio
    async def test_process_checkout_retry_logic(self, inline_client, mock_agent):
        """Test checkout processing with retry logic."""
        inline_client._agent = mock_agent
        inline_client._initialized = True
        inline_client.config.retry_attempts = 2
        
        # Mock response
        mock_response = Mock()
        mock_response.transaction_id = "test-123"
        mock_response.recommendations = []
        mock_agent.process_checkout.return_value = mock_response
        
        # First call fails, second succeeds
        mock_agent.process_checkout.side_effect = [Exception("Network error"), mock_response]
        
        request = Mock()
        response = await inline_client.process_checkout(request)
        
        assert response.transaction_id == "test-123"
        assert mock_agent.process_checkout.call_count == 2
    
    @pytest.mark.asyncio
    async def test_health_check_healthy(self, inline_client):
        """Test health check when client is healthy."""
        inline_client._initialized = True
        inline_client._request_count = 10
        inline_client._error_count = 1
        inline_client._total_latency_ms = 500.0
        
        health = await inline_client.health_check()
        
        assert health["status"] == "healthy"
        assert health["initialized"] is True
        assert health["request_count"] == 10
        assert health["error_count"] == 1
        assert health["average_latency_ms"] == 50.0
    
    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, inline_client):
        """Test health check when client is unhealthy."""
        inline_client._initialized = False
        
        health = await inline_client.health_check()
        
        assert health["status"] == "unhealthy"
        assert health["initialized"] is False
    
    def test_get_metrics(self, inline_client):
        """Test getting performance metrics."""
        inline_client._request_count = 100
        inline_client._error_count = 5
        inline_client._total_latency_ms = 1000.0
        inline_client._circuit_breaker_failures = 2
        
        metrics = inline_client.get_metrics()
        
        assert metrics["request_count"] == 100
        assert metrics["error_count"] == 5
        assert metrics["error_rate"] == 0.05
        assert metrics["average_latency_ms"] == 10.0
        assert metrics["circuit_breaker_failures"] == 2


class TestSyncInlineCheckoutClient:
    """Test synchronous inline checkout client."""
    
    def test_sync_client_initialization(self):
        """Test sync client initialization."""
        client = SyncInlineCheckoutClient()
        
        assert client._client is not None
        assert client._loop is None
    
    def test_sync_client_get_loop(self):
        """Test getting event loop."""
        client = SyncInlineCheckoutClient()
        loop = client._get_loop()
        
        assert loop is not None
        assert client._loop is loop
    
    def test_sync_client_initialize(self):
        """Test sync client initialization."""
        client = SyncInlineCheckoutClient()
        
        with patch.object(client._client, 'initialize', new_callable=AsyncMock) as mock_init:
            client.initialize()
            mock_init.assert_called_once()
    
    def test_sync_client_process_checkout(self):
        """Test sync client checkout processing."""
        client = SyncInlineCheckoutClient()
        
        with patch.object(client._client, 'process_checkout', new_callable=AsyncMock) as mock_process:
            mock_response = Mock()
            mock_process.return_value = mock_response
            
            request = Mock()
            response = client.process_checkout(request)
            
            assert response is mock_response
            mock_process.assert_called_once_with(request, None)
    
    def test_sync_client_health_check(self):
        """Test sync client health check."""
        client = SyncInlineCheckoutClient()
        
        with patch.object(client._client, 'health_check', new_callable=AsyncMock) as mock_health:
            mock_health.return_value = {"status": "healthy"}
            
            health = client.health_check()
            
            assert health["status"] == "healthy"
            mock_health.assert_called_once()
    
    def test_sync_client_get_metrics(self):
        """Test sync client metrics."""
        client = SyncInlineCheckoutClient()
        
        with patch.object(client._client, 'get_metrics') as mock_metrics:
            mock_metrics.return_value = {"request_count": 10}
            
            metrics = client.get_metrics()
            
            assert metrics["request_count"] == 10
            mock_metrics.assert_called_once()
    
    def test_sync_client_cleanup(self):
        """Test sync client cleanup."""
        client = SyncInlineCheckoutClient()
        
        with patch.object(client._client, 'cleanup', new_callable=AsyncMock) as mock_cleanup:
            client.cleanup()
            mock_cleanup.assert_called_once()


class TestConvenienceFunctions:
    """Test convenience functions for inline deployment."""
    
    @pytest.mark.asyncio
    async def test_get_inline_client_singleton(self):
        """Test that get_inline_client returns singleton instance."""
        with patch('deployment.inline.embedded.InlineCheckoutClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            client1 = await get_inline_client()
            client2 = await get_inline_client()
            
            assert client1 is client2
    
    @pytest.mark.asyncio
    async def test_process_checkout_inline(self):
        """Test process_checkout_inline convenience function."""
        with patch('deployment.inline.embedded.get_inline_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.transaction_id = "test-123"
            mock_client.process_checkout.return_value = mock_response
            mock_get_client.return_value = mock_client
            
            request = Mock()
            response = await process_checkout_inline(request)
            
            assert response.transaction_id == "test-123"
            mock_client.process_checkout.assert_called_once_with(request, None)
    
    @pytest.mark.asyncio
    async def test_inline_checkout_client_context_manager(self):
        """Test inline_checkout_client context manager."""
        with patch('deployment.inline.embedded.InlineCheckoutClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            async with inline_checkout_client() as client:
                assert client is mock_client
                mock_client.initialize.assert_called_once()
            
            mock_client.cleanup.assert_called_once()


class TestCircuitBreaker:
    """Test circuit breaker functionality."""
    
    def test_circuit_breaker_open_error(self):
        """Test circuit breaker open error."""
        error = CircuitBreakerOpenError("Circuit breaker is open")
        assert str(error) == "Circuit breaker is open"
        assert isinstance(error, Exception)
