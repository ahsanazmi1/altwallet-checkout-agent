# Orca Alignment Inventory Checklist

This document provides a comprehensive inventory of all references to "AltWallet", "AltWallet Checkout Agent", and related branding that need to be updated for Orca alignment.

## 📋 Summary

- **Total Files with AltWallet References**: 50+ files
- **Total References Found**: 1,200+ instances
- **Categories**: Package names, API titles, Docker labels, Helm charts, documentation, examples, CI/CD, environment variables

---

## 🏷️ Package Names & Module References

### Python Package Structure
- [ ] **`src/altwallet_agent/`** - Main package directory (rename to `orca_checkout`)
- [ ] **`altwallet_merchant_agent/`** - Secondary package directory
- [ ] **`pyproject.toml`** - Package name and metadata
  ```diff
  - name = "altwallet_agent"
  + name = "orca_checkout"
  - description = "AltWallet Checkout Agent - Core Engine MVP"
  + description = "Orca Checkout Agent - Core Engine MVP"
  - authors = [{name = "AltWallet Team", email = "support@altwallet.com"}]
  + authors = [{name = "Orca Team", email = "support@orca.com"}]
  ```

### Node.js Package
- [ ] **`package.json`** - Root package configuration
  ```diff
  - "name": "altwallet-checkout-agent"
  + "name": "orca-checkout-agent"
  - "description": "A checkout agent system for AltWallet payment processing"
  + "description": "A checkout agent system for Orca payment processing"
  ```

### SDK Packages
- [ ] **`sdk/python/setup.py`** - Python SDK
  ```diff
  - name="altwallet-sdk"
  + name="orca-sdk"
  - author="AltWallet Team"
  + author="Orca Team"
  - author_email="team@altwallet.com"
  + author_email="team@orca.com"
  - description="AltWallet Checkout Agent Python SDK"
  + description="Orca Checkout Agent Python SDK"
  ```

- [ ] **`sdk/nodejs/package.json`** - Node.js SDK
  ```diff
  - "name": "altwallet-sdk"
  + "name": "orca-sdk"
  - "description": "AltWallet Checkout Agent Node.js SDK"
  + "description": "Orca Checkout Agent Node.js SDK"
  - "author": "AltWallet Team"
  + "author": "Orca Team"
  ```

---

## 🌐 API & OpenAPI References

### OpenAPI Specification
- [ ] **`openapi/openapi.yaml`** - API specification
  ```diff
  - title: AltWallet Checkout Agent API
  + title: Orca Checkout Agent API
  - description: Core Engine MVP for checkout processing and scoring with intelligent decision-making capabilities.
  + description: Core Engine MVP for checkout processing and scoring with intelligent decision-making capabilities.
  - contact:
  -   name: AltWallet Team
  -   email: support@altwallet.com
  + contact:
  +   name: Orca Team
  +   email: support@orca.com
  - servers:
  -   - url: https://api.altwallet.com/v1
  + servers:
  +   - url: https://api.orca.com/v1
  ```

### API Implementation
- [ ] **`src/altwallet_agent/api.py`** - FastAPI application
  ```diff
  - """FastAPI application for AltWallet Checkout Agent."""
  + """FastAPI application for Orca Checkout Agent."""
  - title="AltWallet Checkout Agent API",
  + title="Orca Checkout Agent API",
  ```

### CLI References
- [ ] **`src/altwallet_agent/cli.py`** - CLI interface
  ```diff
  - AltWallet Checkout Agent CLI
  + Orca Checkout Agent CLI
  - """AltWallet Checkout Agent CLI - Decision Simulation and Management"""
  + """Orca Checkout Agent CLI - Decision Simulation and Management"""
  - click.echo("AltWallet Checkout Agent Health Check")
  + click.echo("Orca Checkout Agent Health Check")
  ```

---

## 🐳 Docker & Container References

### Dockerfile
- [ ] **`Dockerfile`** - Container configuration
  ```diff
  - # Multi-stage Dockerfile for AltWallet Checkout Agent
  + # Multi-stage Dockerfile for Orca Checkout Agent
  - LABEL org.opencontainers.image.title="AltWallet Checkout Agent" \
  + LABEL org.opencontainers.image.title="Orca Checkout Agent" \
  -     org.opencontainers.image.description="Core Engine MVP for checkout processing and scoring" \
  +     org.opencontainers.image.description="Core Engine MVP for checkout processing and scoring" \
  -     org.opencontainers.image.vendor="AltWallet" \
  +     org.opencontainers.image.vendor="Orca" \
  -     org.opencontainers.image.source="https://github.com/altwallet/checkout-agent"
  +     org.opencontainers.image.source="https://github.com/orca/checkout-agent"
  ```

### Docker Compose
- [ ] **`docker-compose.yml`** - Service configuration
  ```diff
  - altwallet-agent-api:
  + orca-agent-api:
  -   image: altwallet/checkout-agent:${VERSION:-0.1.0}
  +   image: orca/checkout-agent:${VERSION:-0.1.0}
  -   container_name: altwallet-agent-api
  +   container_name: orca-agent-api
  -     - "org.opencontainers.image.title=AltWallet Checkout Agent"
  +     - "org.opencontainers.image.title=Orca Checkout Agent"
  -     - "org.opencontainers.image.vendor=AltWallet"
  +     - "org.opencontainers.image.vendor=Orca"
  ```

---

## ☸️ Kubernetes & Helm References

### Helm Chart
- [ ] **`deploy/helm/altwallet-checkout-agent/Chart.yaml`** - Chart metadata
  ```diff
  - name: altwallet-checkout-agent
  + name: orca-checkout-agent
  - description: AltWallet Checkout Agent - Intelligent card recommendations and transaction scoring
  + description: Orca Checkout Agent - Intelligent card recommendations and transaction scoring
  - home: https://github.com/altwallet/checkout-agent
  + home: https://github.com/orca/checkout-agent
  - sources:
  -   - https://github.com/altwallet/checkout-agent
  + sources:
  +   - https://github.com/orca/checkout-agent
  - maintainers:
  -   - name: AltWallet Team
  -     email: team@altwallet.com
  + maintainers:
  +   - name: Orca Team
  +     email: team@orca.com
  - keywords:
  -   - altwallet
  + keywords:
  +   - orca
  ```

### Helm Values
- [ ] **`deploy/helm/altwallet-checkout-agent/values.yaml`** - Chart values
  ```diff
  - # Default values for altwallet-checkout-agent
  + # Default values for orca-checkout-agent
  -   repository: altwallet/checkout-agent
  +   repository: orca/checkout-agent
  -     - host: altwallet-checkout-agent.local
  +     - host: orca-checkout-agent.local
  -         name: altwallet-checkout-agent-secrets
  +         name: orca-checkout-agent-secrets
  -     - containerName: altwallet-checkout-agent
  +     - containerName: orca-checkout-agent
  ```

### Kubernetes Manifests
- [ ] **`deployment/sidecar/kubernetes.yaml`** - K8s deployment
  ```diff
  -   name: altwallet-checkout-agent
  +   name: orca-checkout-agent
  -     app: altwallet-checkout-agent
  +     app: orca-checkout-agent
  -       app: altwallet-checkout-agent
  +       app: orca-checkout-agent
  -       - name: altwallet-checkout-agent
  -         image: altwallet/checkout-agent:latest
  +       - name: orca-checkout-agent
  +         image: orca/checkout-agent:latest
  ```

---

## 🏗️ Infrastructure as Code

### Terraform
- [ ] **`deploy/terraform/`** - All Terraform files
  ```diff
  - project_name = "altwallet-checkout-agent"
  + project_name = "orca-checkout-agent"
  - container_image = "altwallet/checkout-agent"
  + container_image = "orca/checkout-agent"
  - domain_name = "checkout.altwallet.com"
  + domain_name = "checkout.orca.com"
  - alert_email = "alerts@altwallet.com"
  + alert_email = "alerts@orca.com"
  ```

### Deployment Configurations
- [ ] **`deployment/config.py`** - Deployment settings
  ```diff
  - default="altwallet-checkout-agent", description="Container name"
  + default="orca-checkout-agent", description="Container name"
  ```

---

## 📚 Documentation References

### README Files
- [ ] **`README.md`** - Main documentation
  ```diff
  - # AltWallet Checkout Agent
  + # Orca Checkout Agent
  - AltWallet Checkout Agent is a production-minded Python scaffold for intelligent checkout processing and card recommendations.
  + Orca Checkout Agent is a production-minded Python scaffold for intelligent checkout processing and card recommendations.
  - Phase 4 has successfully transformed the AltWallet Checkout Agent into a production-ready platform
  + Phase 4 has successfully transformed the Orca Checkout Agent into a production-ready platform
  - from altwallet_sdk import AltWalletClient
  + from orca_sdk import OrcaClient
  - client = AltWalletClient(api_key="your-api-key")
  + client = OrcaClient(api_key="your-api-key")
  - const client = new AltWalletClient({
  + const client = new OrcaClient({
  - baseUrl: 'https://api.altwallet.com'
  + baseUrl: 'https://api.orca.com'
  - helm repo add altwallet https://charts.altwallet.com
  + helm repo add orca https://charts.orca.com
  - helm install checkout-agent altwallet/altwallet-checkout-agent
  + helm install checkout-agent orca/orca-checkout-agent
  ```

### SDK Documentation
- [ ] **`sdk/README.md`** - SDK overview
- [ ] **`sdk/python/README.md`** - Python SDK docs
- [ ] **`sdk/nodejs/README.md`** - Node.js SDK docs

### Technical Documentation
- [ ] **`docs/certification.md`** - Certification procedures
- [ ] **`docs/CERTIFICATION_CHECKLIST.md`** - Certification checklist
- [ ] **`deploy/README.md`** - Deployment guide
- [ ] **`deploy/helm/README.md`** - Helm deployment guide
- [ ] **`deploy/terraform/README.md`** - Terraform deployment guide

---

## 🔧 Environment Variables & Configuration

### Environment Variable Prefixes
- [ ] **`main.py`** - Environment configuration
  ```diff
  - "endpoint": os.getenv("ALTWALLET_ENDPOINT", "https://api.altwallet.com"),
  + "endpoint": os.getenv("ORCA_ENDPOINT", "https://api.orca.com"),
  ```

- [ ] **`src/agent.js`** - Node.js configuration
  ```diff
  - endpoint: process.env.ALTWALLET_ENDPOINT || 'https://api.altwallet.com',
  + endpoint: process.env.ORCA_ENDPOINT || 'https://api.orca.com',
  ```

- [ ] **`tests/setup.js`** - Test configuration
  ```diff
  - process.env.ALTWALLET_ENDPOINT = 'https://test-api.altwallet.com';
  + process.env.ORCA_ENDPOINT = 'https://test-api.orca.com';
  ```

### Package Init Files
- [ ] **`src/altwallet_agent/__init__.py`** - Package metadata
  ```diff
  - __email__ = "support@altwallet.com"
  + __email__ = "support@orca.com"
  ```

- [ ] **`altwallet_merchant_agent/__init__.py`** - Secondary package
  ```diff
  - __email__ = "support@altwallet.com"
  + __email__ = "support@orca.com"
  ```

---

## 🧪 Test Files & Examples

### Test Files (1,200+ references)
- [ ] **All test files in `tests/`** - Update import statements and references
  ```diff
  - from altwallet_agent.api import app
  + from orca_checkout.api import app
  - from altwallet_agent.cli import (
  + from orca_checkout.cli import (
  - @patch("altwallet_agent.api.get_logger")
  + @patch("orca_checkout.api.get_logger")
  ```

### Example Files
- [ ] **`examples/`** - All example files and demos
- [ ] **`examples/deploy/`** - Deployment examples
- [ ] **`examples/deploy/sidecar_docker_compose.yml`**
- [ ] **`examples/deploy/sidecar_config.json`**

---

## 🔄 CI/CD & Workflows

### GitHub Actions
- [ ] **`.github/workflows/ci.yml`** - CI pipeline
- [ ] **`.github/workflows/test.yml`** - Test pipeline  
- [ ] **`.github/workflows/phase4-guardrails.yml`** - Phase 4 checks

### Build Scripts
- [ ] **`scripts/`** - All build and deployment scripts
- [ ] **`Makefile`** - Unix/Linux build tasks
- [ ] **`tasks.ps1`** - Windows PowerShell tasks
- [ ] **`setup.ps1`** - Windows setup script

---

## 📦 Import Statements & Module References

### Python Imports (500+ references)
- [ ] **All Python files** - Update import statements
  ```diff
  - from altwallet_agent.analytics import log_decision_outcome
  + from orca_checkout.analytics import log_decision_outcome
  - from altwallet_agent.composite_utility import CompositeUtility
  + from orca_checkout.composite_utility import CompositeUtility
  - from altwallet_agent.decisioning import (
  + from orca_checkout.decisioning import (
  - from altwallet_agent.logger import (
  + from orca_checkout.logger import (
  - from altwallet_agent.models import Context
  + from orca_checkout.models import Context
  - from altwallet_agent.scoring import score_transaction
  + from orca_checkout.scoring import score_transaction
  ```

### Logger Configuration
- [ ] **`src/altwallet_agent/logger.py`** - Logging setup
  ```diff
  - """Structured logging configuration for AltWallet Checkout Agent.
  + """Structured logging configuration for Orca Checkout Agent.
  - self._logger = logging.getLogger(name or "altwallet_agent")
  + self._logger = logging.getLogger(name or "orca_checkout")
  - "altwallet_agent",
  - "altwallet_agent.scoring",
  - "altwallet_agent.decisioning",
  - "altwallet_agent.webhooks",
  - "altwallet_agent.analytics",
  + "orca_checkout",
  + "orca_checkout.scoring",
  + "orca_checkout.decisioning",
  + "orca_checkout.webhooks",
  + "orca_checkout.analytics",
  ```

---

## 🌍 Domain & URL References

### API Endpoints
- [ ] **All files** - Update domain references
  ```diff
  - https://api.altwallet.com
  + https://api.orca.com
  - https://charts.altwallet.com
  + https://charts.orca.com
  - checkout.altwallet.com
  + checkout.orca.com
  - support@altwallet.com
  + support@orca.com
  - team@altwallet.com
  + team@orca.com
  - alerts@altwallet.com
  + alerts@orca.com
  ```

### GitHub Repository References
- [ ] **All files** - Update repository URLs
  ```diff
  - https://github.com/altwallet/checkout-agent
  + https://github.com/orca/checkout-agent
  ```

---

## 📋 Migration Strategy

### Phase 1: Non-Breaking Changes
1. **Package Structure**: Keep `altwallet_agent` package name, add compatibility shim
2. **Environment Variables**: Support both `ALTWALLET_*` and `ORCA_*` prefixes
3. **API Endpoints**: Maintain backward compatibility for existing integrations
4. **Docker Images**: Tag with both old and new names during transition

### Phase 2: Breaking Changes
1. **Package Rename**: `altwallet_agent` → `orca_checkout`
2. **Import Paths**: Update all import statements
3. **Environment Variables**: Deprecate `ALTWALLET_*` prefixes
4. **API Endpoints**: Update to new Orca domains

### Phase 3: Cleanup
1. **Remove Deprecated**: Remove old branding and compatibility shims
2. **Update Documentation**: Final pass on all documentation
3. **Release**: Tag as v1.1.0-orca.0

---

## ✅ Completion Checklist

- [ ] **Package Names**: Update all package.json, setup.py, pyproject.toml files
- [ ] **API Titles**: Update OpenAPI spec and FastAPI app titles
- [ ] **Docker Labels**: Update all container labels and metadata
- [ ] **Helm Charts**: Update chart names, descriptions, and values
- [ ] **Documentation**: Update all README files and documentation
- [ ] **Environment Variables**: Add ORCA_ prefix with backward compatibility
- [ ] **Import Statements**: Update all Python import statements
- [ ] **Test Files**: Update all test imports and references
- [ ] **CI/CD**: Update workflow files and build scripts
- [ ] **Examples**: Update all example files and demos
- [ ] **Domain References**: Update all URLs and email addresses
- [ ] **Migration Guide**: Create MIGRATION.md with deprecation timeline

---

## 🚨 Critical Files (High Priority)

1. **`pyproject.toml`** - Core package configuration
2. **`README.md`** - Main documentation
3. **`openapi/openapi.yaml`** - API specification
4. **`Dockerfile`** - Container metadata
5. **`deploy/helm/altwallet-checkout-agent/Chart.yaml`** - Helm chart
6. **`src/altwallet_agent/api.py`** - API implementation
7. **`src/altwallet_agent/cli.py`** - CLI interface
8. **All test files** - Import statements and references

---

*This inventory was generated on the `orca-phase-align` branch and represents a comprehensive scan of the codebase for AltWallet branding references.*
