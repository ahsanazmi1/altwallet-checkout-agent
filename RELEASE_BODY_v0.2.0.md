# Phase 2 — Intelligence Layer (v0.2.0)

## What's new

- **Probabilistic approval odds** (rules → calibrated logistic)
- **Preference & loyalty weighting** + merchant-preferred network penalties
- **Composite utility** = p_approval * expected_rewards * preference_weight * merchant_penalty
- **Explainability**: additive feature attributions (top ± drivers) + audit block
- **OpenAPI v1.0**: /v1/score, /v1/explain, /healthz, /version
- **Reproducible tests**: golden fixtures, snapshots, smoke tests in CI
- **CLI**: JSON output with Phase-2 fields; structured logs

## Artifacts

- **openapi/openapi.json** (v1.0.0)
- **Docker image**: ghcr.io/ahsanazmi1/altwallet-checkout-agent:v0.2.0
- **Configs**: config/approval.yaml, config/preferences.yaml
- **Golden fixtures & snapshots** under tests/golden/

## Verify locally

```bash
# Run all tests
pytest -vv

# Run smoke tests
python smoke_tests.py

# Test CLI with JSON output
python -m altwallet_agent score --input examples/context_basic.json --json

# Test API endpoints
curl http://localhost:8000/health
curl -X POST "http://localhost:8000/v1/score" \
  -H "Content-Type: application/json" \
  -d @examples/context_basic.json
```

## Breaking changes

None expected. Response now includes explainability and audit. Consumers should ignore unknown fields if parsing strictly.

## Checksums

### Docker Image
- **ghcr.io/ahsanazmi1/altwallet-checkout-agent:v0.2.0**
- SHA256: (to be provided after build)

### Key Files
- **openapi/openapi.json**: SHA256: `DB10C3C0910F80665910DEBCF06CEB5D670B9B80CEDFECCD42129913E406AB70`
- **config/approval.yaml**: SHA256: `BE80640550F1C0B9818297F4CF1BF070193A49DC6AFBC44B56DE73E6D163EF5D`
- **config/preferences.yaml**: SHA256: `C8D2DE57BEF7F7D3EA12A5E9DE0B85528DA75DEFE953BD64B6DADCD27DAD9DD5`

## Quick Start

```bash
# Pull and run Docker image
docker pull ghcr.io/ahsanazmi1/altwallet-checkout-agent:v0.2.0
docker run -p 8000:8000 ghcr.io/ahsanazmi1/altwallet-checkout-agent:v0.2.0

# Or install locally
pip install -e .
python -m altwallet_agent.api
```

## Documentation

- **API Docs**: http://localhost:8000/docs (when running)
- **Postman Collection**: `openapi/AltWallet_Checkout_Agent_v0.2.0.postman_collection.json`
- **Full Release Notes**: [RELEASE_v0.2.0.md](RELEASE_v0.2.0.md)
