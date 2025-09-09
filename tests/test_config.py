"""
Tests for Orca configuration management with backward compatibility.
"""

import os
import warnings
import pytest
from unittest.mock import patch

from altwallet_agent.config import OrcaConfig, get_config


class TestOrcaConfig:
    """Test the Orca configuration system."""
    
    def test_orca_prefix_takes_priority(self):
        """Test that ORCA_ prefixed variables take priority over legacy ones."""
        with patch.dict(os.environ, {
            'ORCA_API_KEY': 'orca_key',
            'ALTWALLET_API_KEY': 'legacy_key',
            'ORCA_ENDPOINT': 'https://api.orca.com',
            'ALTWALLET_ENDPOINT': 'https://api.altwallet.com'
        }):
            config = OrcaConfig()
            assert config.api_key == 'orca_key'
            assert config.api_endpoint == 'https://api.orca.com'
    
    def test_legacy_fallback_with_deprecation_warning(self):
        """Test that legacy variables are used as fallback with deprecation warning."""
        with patch.dict(os.environ, {
            'ALTWALLET_API_KEY': 'legacy_key',
            'ALTWALLET_ENDPOINT': 'https://api.altwallet.com'
        }, clear=True):
            config = OrcaConfig()
            
            # Capture warnings
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                api_key = config.api_key
                api_endpoint = config.api_endpoint
                
                # Check that deprecation warnings were issued
                assert len(w) == 2
                assert any("ALTWALLET_API_KEY is deprecated" in str(warning.message) for warning in w)
                assert any("ALTWALLET_ENDPOINT is deprecated" in str(warning.message) for warning in w)
                
                # Check that legacy values are used
                assert api_key == 'legacy_key'
                assert api_endpoint == 'https://api.altwallet.com'
    
    def test_default_values(self):
        """Test that default values are used when no environment variables are set."""
        with patch.dict(os.environ, {}, clear=True):
            config = OrcaConfig()
            assert config.api_endpoint == 'https://api.orca.com'
            assert config.timeout == 30000
            assert config.log_level == 'INFO'
            assert config.deployment_mode == 'sidecar'
            assert config.environment == 'development'
            assert config.database_pool_size == 10
            assert config.enable_metrics is True
            assert config.enable_analytics is True
    
    def test_type_conversion(self):
        """Test that environment variables are converted to correct types."""
        with patch.dict(os.environ, {
            'ORCA_TIMEOUT': '5000',
            'ORCA_DATABASE_POOL_SIZE': '20',
            'ORCA_ENABLE_METRICS': 'false',
            'ORCA_CORS_ORIGINS': 'https://app.orca.com,https://admin.orca.com'
        }, clear=True):
            config = OrcaConfig()
            assert isinstance(config.timeout, int)
            assert config.timeout == 5000
            assert isinstance(config.database_pool_size, int)
            assert config.database_pool_size == 20
            assert isinstance(config.enable_metrics, bool)
            assert config.enable_metrics is False
            assert isinstance(config.cors_origins, list)
            assert config.cors_origins == ['https://app.orca.com', 'https://admin.orca.com']
    
    def test_boolean_conversion(self):
        """Test boolean conversion for various truthy/falsy values."""
        test_cases = [
            ('true', True),
            ('True', True),
            ('TRUE', True),
            ('1', True),
            ('yes', True),
            ('on', True),
            ('enabled', True),
            ('false', False),
            ('False', False),
            ('FALSE', False),
            ('0', False),
            ('no', False),
            ('off', False),
            ('disabled', False),
        ]
        
        for value, expected in test_cases:
            with patch.dict(os.environ, {'ORCA_ENABLE_METRICS': value}, clear=True):
                config = OrcaConfig()
                assert config.enable_metrics == expected, f"Failed for value: {value}"
    
    def test_deprecation_warning_only_issued_once(self):
        """Test that deprecation warnings are only issued once per variable."""
        with patch.dict(os.environ, {
            'ALTWALLET_API_KEY': 'legacy_key'
        }, clear=True):
            config = OrcaConfig()
            
            # First access should issue warning
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                config.api_key
                assert len(w) == 1
                assert "ALTWALLET_API_KEY is deprecated" in str(w[0].message)
            
            # Second access should not issue warning
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                config.api_key
                assert len(w) == 0
    
    def test_to_dict(self):
        """Test that configuration can be converted to dictionary."""
        with patch.dict(os.environ, {
            'ORCA_API_KEY': 'test_key',
            'ORCA_ENDPOINT': 'https://test.orca.com',
            'ORCA_TIMEOUT': '5000'
        }, clear=True):
            config = OrcaConfig()
            config_dict = config.to_dict()
            
            assert isinstance(config_dict, dict)
            assert config_dict['api_key'] == 'test_key'
            assert config_dict['api_endpoint'] == 'https://test.orca.com'
            assert config_dict['timeout'] == 5000
            assert 'log_level' in config_dict
            assert 'deployment_mode' in config_dict
    
    def test_get_config_singleton(self):
        """Test that get_config returns a singleton instance."""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2
    
    def test_legacy_variable_mapping(self):
        """Test all legacy variable mappings."""
        legacy_mappings = [
            ('ALTWALLET_API_KEY', 'api_key'),
            ('ALTWALLET_ENDPOINT', 'api_endpoint'),
            ('REQUEST_TIMEOUT', 'timeout'),
            ('LOG_LEVEL', 'log_level'),
            ('LOG_FORMAT', 'log_format'),
            ('DEPLOYMENT_MODE', 'deployment_mode'),
            ('ENVIRONMENT', 'environment'),
            ('DATABASE_URL', 'database_url'),
            ('DATABASE_POOL_SIZE', 'database_pool_size'),
            ('DATABASE_MAX_OVERFLOW', 'database_max_overflow'),
            ('REDIS_URL', 'redis_url'),
            ('REDIS_POOL_SIZE', 'redis_pool_size'),
            ('REDIS_MAX_CONNECTIONS', 'redis_max_connections'),
            ('ENABLE_METRICS', 'enable_metrics'),
            ('METRICS_PORT', 'metrics_port'),
            ('HEALTH_CHECK_INTERVAL', 'health_check_interval'),
            ('JWT_SECRET', 'jwt_secret'),
            ('ENCRYPTION_KEY', 'encryption_key'),
            ('CORS_ORIGINS', 'cors_origins'),
            ('ENABLE_ANALYTICS', 'enable_analytics'),
            ('ENABLE_WEBHOOKS', 'enable_webhooks'),
            ('ENABLE_CACHING', 'enable_caching'),
            ('CACHE_TTL', 'cache_ttl'),
            ('MAX_WORKERS', 'max_workers'),
            ('REQUEST_TIMEOUT', 'request_timeout'),
            ('RATE_LIMIT', 'rate_limit'),
        ]
        
        for legacy_var, property_name in legacy_mappings:
            with patch.dict(os.environ, {legacy_var: 'test_value'}, clear=True):
                config = OrcaConfig()
                with warnings.catch_warnings(record=True) as w:
                    warnings.simplefilter("always")
                    value = getattr(config, property_name)
                    assert len(w) == 1
                    assert f"{legacy_var} is deprecated" in str(w[0].message)
                    assert value == 'test_value'


class TestConfigurationIntegration:
    """Test configuration integration with existing code."""
    
    def test_main_py_integration(self):
        """Test that main.py uses the new configuration system."""
        with patch.dict(os.environ, {
            'ORCA_API_KEY': 'test_key',
            'ORCA_ENDPOINT': 'https://test.orca.com',
            'ORCA_TIMEOUT': '5000'
        }, clear=True):
            from main import CheckoutAgent
            agent = CheckoutAgent()
            
            assert agent.config['api_key'] == 'test_key'
            assert agent.config['endpoint'] == 'https://test.orca.com'
            assert agent.config['timeout'] == 5000
    
    def test_legacy_compatibility_in_main(self):
        """Test that main.py still works with legacy environment variables."""
        with patch.dict(os.environ, {
            'ALTWALLET_API_KEY': 'legacy_key',
            'ALTWALLET_ENDPOINT': 'https://legacy.altwallet.com',
            'REQUEST_TIMEOUT': '10000'
        }, clear=True):
            from main import CheckoutAgent
            agent = CheckoutAgent()
            
            assert agent.config['api_key'] == 'legacy_key'
            assert agent.config['endpoint'] == 'https://legacy.altwallet.com'
            assert agent.config['timeout'] == 10000


if __name__ == '__main__':
    pytest.main([__file__])
