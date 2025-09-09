# Migration Guide: AltWallet → Orca

This document outlines the migration from AltWallet Checkout Agent to Orca Checkout Agent.

## 🚀 Overview

The AltWallet Checkout Agent has been rebranded to **Orca Checkout Agent** as part of our platform evolution. This migration maintains backward compatibility where possible while introducing the new Orca branding.

## 📦 Package Changes

### Python Package
- **Old**: `altwallet_agent`
- **New**: `orca_checkout`
- **Compatibility**: A compatibility shim is provided at the root level

### Node.js Package
- **Old**: `altwallet-checkout-agent`
- **New**: `orca-checkout-agent`

### SDK Packages
- **Python SDK**: `altwallet-sdk` → `orca-sdk`
- **Node.js SDK**: `altwallet-sdk` → `orca-sdk`

## 🔄 Import Changes

### Python Imports
```python
# OLD (deprecated but supported)
from altwallet_agent import CheckoutAgent
from altwallet_agent.api import app
from altwallet_agent.cli import cli

# NEW (recommended)
from orca_checkout import CheckoutAgent
from orca_checkout.api import app
from orca_checkout.cli import cli
```

### Node.js Imports
```javascript
// OLD (deprecated but supported)
const { AltWalletClient } = require('altwallet-sdk');

// NEW (recommended)
const { OrcaClient } = require('orca-sdk');
```

## 🌐 API Changes

### API Title
- **Old**: "AltWallet Checkout Agent API"
- **New**: "Orca Checkout Agent API"

### Server Endpoints
- **Old**: `https://api.altwallet.com/v1`
- **New**: `https://api.orca.com/v1`

### Contact Information
- **Old**: `support@altwallet.com`
- **New**: `support@orca.com`

## 🐳 Container Changes

### Docker Images
- **Old**: `altwallet/checkout-agent:latest`
- **New**: `orca/checkout-agent:latest`

### Container Labels
- **Title**: "AltWallet Checkout Agent" → "Orca Checkout Agent"
- **Vendor**: "AltWallet" → "Orca"
- **Source**: `https://github.com/altwallet/checkout-agent` → `https://github.com/orca/checkout-agent`

## ☸️ Kubernetes & Helm Changes

### Helm Chart
- **Chart Name**: `altwallet-checkout-agent` → `orca-checkout-agent`
- **Repository**: `altwallet/checkout-agent` → `orca/checkout-agent`

### Kubernetes Resources
- **Service Names**: `altwallet-checkout-agent` → `orca-checkout-agent`
- **Container Names**: `altwallet-checkout-agent` → `orca-checkout-agent`
- **Secret Names**: `altwallet-checkout-agent-secrets` → `orca-checkout-agent-secrets`

## 🔧 Environment Variables

### New Environment Variables (Recommended)
```bash
# API Configuration
ORCA_ENDPOINT=https://api.orca.com
ORCA_API_KEY=your-api-key

# Application Configuration
ORCA_LOG_LEVEL=INFO
ORCA_DEPLOYMENT_MODE=sidecar
```

### Legacy Environment Variables (Deprecated)
```bash
# These will continue to work but are deprecated
ALTWALLET_ENDPOINT=https://api.altwallet.com
ALTWALLET_API_KEY=your-api-key
```

**Migration**: Update your environment variables to use the `ORCA_` prefix. The old `ALTWALLET_` variables will continue to work but will log deprecation warnings.

## 📚 Documentation Updates

### README Files
All documentation has been updated to reflect the Orca branding:
- Main README.md
- SDK documentation
- Deployment guides
- API documentation

### URLs and Links
- **GitHub Repository**: `https://github.com/altwallet/checkout-agent` → `https://github.com/orca/checkout-agent`
- **Chart Repository**: `https://charts.altwallet.com` → `https://charts.orca.com`
- **Documentation**: All links updated to Orca domains

## 🧪 Testing Changes

### Test Imports
```python
# OLD
from altwallet_agent.api import app
from altwallet_agent.cli import cli

# NEW
from orca_checkout.api import app
from orca_checkout.cli import cli
```

### Test Configuration
```javascript
// OLD
process.env.ALTWALLET_ENDPOINT = 'https://test-api.altwallet.com';

// NEW
process.env.ORCA_ENDPOINT = 'https://test-api.orca.com';
```

## 🚨 Breaking Changes

### Package Structure
- The main package directory remains `src/altwallet_agent/` for now to maintain compatibility
- Future versions will rename this to `src/orca_checkout/`

### CLI Commands
- CLI commands remain the same: `altwallet_agent` (for backward compatibility)
- Future versions will introduce `orca_checkout` command

## 📋 Migration Checklist

### For Application Developers
- [ ] Update import statements to use `orca_checkout`
- [ ] Update environment variables to use `ORCA_` prefix
- [ ] Update API endpoints to use `api.orca.com`
- [ ] Update Docker images to use `orca/checkout-agent`
- [ ] Update Helm chart references to `orca-checkout-agent`

### For Infrastructure Teams
- [ ] Update Kubernetes manifests
- [ ] Update Helm chart installations
- [ ] Update Terraform configurations
- [ ] Update CI/CD pipelines
- [ ] Update monitoring and alerting

### For SDK Users
- [ ] Update package dependencies
- [ ] Update import statements
- [ ] Update client initialization code
- [ ] Update API endpoint configurations

## 🔄 Rollback Plan

If you need to rollback to the previous version:

1. **Revert Docker Images**: Use `altwallet/checkout-agent:latest`
2. **Revert Environment Variables**: Use `ALTWALLET_` prefixes
3. **Revert API Endpoints**: Use `api.altwallet.com`
4. **Revert Helm Charts**: Use `altwallet-checkout-agent`

## 📞 Support

- **Email**: support@orca.com
- **Documentation**: [GitHub Repository](https://github.com/orca/checkout-agent)
- **Issues**: [GitHub Issues](https://github.com/orca/checkout-agent/issues)

## 🗓️ Timeline

- **v1.1.0-orca.0**: Initial Orca branding with backward compatibility
- **v1.2.0**: Remove compatibility shims and deprecated features
- **v2.0.0**: Complete migration to Orca branding

---

*This migration guide will be updated as we progress through the Orca alignment phases.*
