# Environment Variables - Orca Checkout Agent

This document describes the environment variables used by the Orca Checkout Agent, including the migration from legacy AltWallet variables to the new ORCA_ prefixed variables.

## 🐋 New ORCA_ Variables (Recommended)

The Orca Checkout Agent now uses `ORCA_` prefixed environment variables. These are the recommended variables to use going forward.

### API Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `ORCA_API_KEY` | API key for authentication | None | `orca_live_1234567890abcdef` |
| `ORCA_ENDPOINT` | API endpoint URL | `https://api.orca.com` | `https://api.orca.com` |
| `ORCA_TIMEOUT` | Request timeout in milliseconds | `30000` | `5000` |

### Application Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `ORCA_LOG_LEVEL` | Logging level | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `ORCA_LOG_FORMAT` | Log format | `json` | `json`, `text` |
| `ORCA_DEPLOYMENT_MODE` | Deployment mode | `sidecar` | `sidecar`, `inline`, `standalone` |
| `ORCA_ENVIRONMENT` | Environment name | `development` | `development`, `staging`, `production` |

### Database Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `ORCA_DATABASE_URL` | Database connection URL | None | `postgresql://user:pass@localhost:5432/orca` |
| `ORCA_DATABASE_POOL_SIZE` | Database pool size | `10` | `20` |
| `ORCA_DATABASE_MAX_OVERFLOW` | Database max overflow | `20` | `30` |

### Redis Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `ORCA_REDIS_URL` | Redis connection URL | None | `redis://localhost:6379/0` |
| `ORCA_REDIS_POOL_SIZE` | Redis pool size | `10` | `20` |
| `ORCA_REDIS_MAX_CONNECTIONS` | Redis max connections | `20` | `50` |

### Monitoring Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `ORCA_ENABLE_METRICS` | Enable metrics collection | `true` | `true`, `false` |
| `ORCA_METRICS_PORT` | Metrics server port | `9090` | `9091` |
| `ORCA_HEALTH_CHECK_INTERVAL` | Health check interval (seconds) | `30` | `60` |

### Security Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `ORCA_JWT_SECRET` | JWT signing secret | None | `your-jwt-secret-here` |
| `ORCA_ENCRYPTION_KEY` | Encryption key | None | `your-encryption-key-here` |
| `ORCA_CORS_ORIGINS` | CORS allowed origins (comma-separated) | `[]` | `https://app.orca.com,https://admin.orca.com` |

### Feature Flags

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `ORCA_ENABLE_ANALYTICS` | Enable analytics | `true` | `true`, `false` |
| `ORCA_ENABLE_WEBHOOKS` | Enable webhooks | `true` | `true`, `false` |
| `ORCA_ENABLE_CACHING` | Enable caching | `true` | `true`, `false` |
| `ORCA_CACHE_TTL` | Cache TTL in seconds | `300` | `600` |

### Performance Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `ORCA_MAX_WORKERS` | Maximum number of workers | `4` | `8` |
| `ORCA_REQUEST_TIMEOUT` | Request timeout in seconds | `30` | `60` |
| `ORCA_RATE_LIMIT` | Rate limit per minute | `1000` | `2000` |

## 🔄 Legacy Variables (Deprecated)

The following legacy variables are still supported but deprecated. They will be removed in a future version.

### Legacy API Configuration

| Legacy Variable | New Variable | Status |
|-----------------|--------------|--------|
| `ALTWALLET_API_KEY` | `ORCA_API_KEY` | ⚠️ Deprecated |
| `ALTWALLET_ENDPOINT` | `ORCA_ENDPOINT` | ⚠️ Deprecated |

### Legacy Application Configuration

| Legacy Variable | New Variable | Status |
|-----------------|--------------|--------|
| `LOG_LEVEL` | `ORCA_LOG_LEVEL` | ⚠️ Deprecated |
| `LOG_FORMAT` | `ORCA_LOG_FORMAT` | ⚠️ Deprecated |
| `DEPLOYMENT_MODE` | `ORCA_DEPLOYMENT_MODE` | ⚠️ Deprecated |
| `ENVIRONMENT` | `ORCA_ENVIRONMENT` | ⚠️ Deprecated |

### Legacy Database Configuration

| Legacy Variable | New Variable | Status |
|-----------------|--------------|--------|
| `DATABASE_URL` | `ORCA_DATABASE_URL` | ⚠️ Deprecated |
| `DATABASE_POOL_SIZE` | `ORCA_DATABASE_POOL_SIZE` | ⚠️ Deprecated |
| `DATABASE_MAX_OVERFLOW` | `ORCA_DATABASE_MAX_OVERFLOW` | ⚠️ Deprecated |

### Legacy Redis Configuration

| Legacy Variable | New Variable | Status |
|-----------------|--------------|--------|
| `REDIS_URL` | `ORCA_REDIS_URL` | ⚠️ Deprecated |
| `REDIS_POOL_SIZE` | `ORCA_REDIS_POOL_SIZE` | ⚠️ Deprecated |
| `REDIS_MAX_CONNECTIONS` | `ORCA_REDIS_MAX_CONNECTIONS` | ⚠️ Deprecated |

### Legacy Monitoring Configuration

| Legacy Variable | New Variable | Status |
|-----------------|--------------|--------|
| `ENABLE_METRICS` | `ORCA_ENABLE_METRICS` | ⚠️ Deprecated |
| `METRICS_PORT` | `ORCA_METRICS_PORT` | ⚠️ Deprecated |
| `HEALTH_CHECK_INTERVAL` | `ORCA_HEALTH_CHECK_INTERVAL` | ⚠️ Deprecated |

### Legacy Security Configuration

| Legacy Variable | New Variable | Status |
|-----------------|--------------|--------|
| `JWT_SECRET` | `ORCA_JWT_SECRET` | ⚠️ Deprecated |
| `ENCRYPTION_KEY` | `ORCA_ENCRYPTION_KEY` | ⚠️ Deprecated |
| `CORS_ORIGINS` | `ORCA_CORS_ORIGINS` | ⚠️ Deprecated |

### Legacy Feature Flags

| Legacy Variable | New Variable | Status |
|-----------------|--------------|--------|
| `ENABLE_ANALYTICS` | `ORCA_ENABLE_ANALYTICS` | ⚠️ Deprecated |
| `ENABLE_WEBHOOKS` | `ORCA_ENABLE_WEBHOOKS` | ⚠️ Deprecated |
| `ENABLE_CACHING` | `ORCA_ENABLE_CACHING` | ⚠️ Deprecated |
| `CACHE_TTL` | `ORCA_CACHE_TTL` | ⚠️ Deprecated |

### Legacy Performance Configuration

| Legacy Variable | New Variable | Status |
|-----------------|--------------|--------|
| `MAX_WORKERS` | `ORCA_MAX_WORKERS` | ⚠️ Deprecated |
| `REQUEST_TIMEOUT` | `ORCA_REQUEST_TIMEOUT` | ⚠️ Deprecated |
| `RATE_LIMIT` | `ORCA_RATE_LIMIT` | ⚠️ Deprecated |

## 🔧 Configuration Priority

The configuration system follows this priority order:

1. **ORCA_ prefixed variables** (highest priority)
2. **Legacy variables** (with deprecation warnings)
3. **Default values** (lowest priority)

### Example

```bash
# If both are set, ORCA_API_KEY takes priority
export ORCA_API_KEY="orca_key"
export ALTWALLET_API_KEY="legacy_key"

# The application will use "orca_key" and issue a deprecation warning
# for ALTWALLET_API_KEY being set but not used
```

## 🚨 Deprecation Warnings

When legacy variables are used, the application will issue deprecation warnings:

### Python

```python
import warnings
warnings.warn(
    "Environment variable 'ALTWALLET_API_KEY' is deprecated. "
    "Please use 'ORCA_API_KEY' instead. "
    "This will be removed in a future version.",
    DeprecationWarning
)
```

### Node.js

```javascript
console.warn('⚠️  DEPRECATED: ALTWALLET_API_KEY is deprecated. Please use ORCA_API_KEY instead.');
```

## 📋 Migration Checklist

### For Application Developers

- [ ] Update environment variable names to use `ORCA_` prefix
- [ ] Update deployment scripts and configuration files
- [ ] Update CI/CD pipeline environment variables
- [ ] Update Docker Compose files and Kubernetes manifests
- [ ] Update documentation and runbooks
- [ ] Test with new environment variables
- [ ] Remove legacy environment variables from production

### For Infrastructure Teams

- [ ] Update Kubernetes ConfigMaps and Secrets
- [ ] Update Helm chart values
- [ ] Update Terraform configurations
- [ ] Update monitoring and alerting configurations
- [ ] Update backup and disaster recovery procedures
- [ ] Update security scanning and compliance checks

### For DevOps Teams

- [ ] Update deployment scripts
- [ ] Update environment provisioning
- [ ] Update monitoring dashboards
- [ ] Update log aggregation and analysis
- [ ] Update performance monitoring
- [ ] Update security monitoring

## 🧪 Testing Configuration

### Development Environment

```bash
# .env.development
ORCA_ENDPOINT=http://localhost:8000
ORCA_LOG_LEVEL=DEBUG
ORCA_ENVIRONMENT=development
ORCA_DEPLOYMENT_MODE=inline
```

### Testing Environment

```bash
# .env.test
ORCA_ENDPOINT=https://test-api.orca.com
ORCA_LOG_LEVEL=WARNING
ORCA_ENVIRONMENT=test
ORCA_DEPLOYMENT_MODE=inline
ORCA_ENABLE_ANALYTICS=false
ORCA_ENABLE_WEBHOOKS=false
```

### Production Environment

```bash
# .env.production
ORCA_ENDPOINT=https://api.orca.com
ORCA_LOG_LEVEL=INFO
ORCA_ENVIRONMENT=production
ORCA_DEPLOYMENT_MODE=sidecar
ORCA_ENABLE_METRICS=true
ORCA_ENABLE_ANALYTICS=true
ORCA_ENABLE_WEBHOOKS=true
```

## 🔍 Configuration Validation

The configuration system includes built-in validation:

- **Type checking**: Environment variables are converted to appropriate types
- **Range validation**: Numeric values are validated against reasonable ranges
- **Format validation**: URLs and other formatted values are validated
- **Dependency checking**: Related configuration values are validated together

### Example Validation

```python
from altwallet_agent.config import get_config

config = get_config()

# This will raise an error if ORCA_TIMEOUT is not a valid integer
timeout = config.timeout

# This will raise an error if ORCA_ENABLE_METRICS is not a valid boolean
metrics_enabled = config.enable_metrics
```

## 📚 Additional Resources

- [Migration Guide](MIGRATION.md) - Complete migration instructions
- [Configuration Examples](config/env.example) - Example configuration files
- [API Documentation](openapi/openapi.yaml) - Complete API specification
- [Deployment Guide](docs/DEPLOYMENT.md) - Deployment instructions

---

*This document will be updated as new environment variables are added or existing ones are modified.*
