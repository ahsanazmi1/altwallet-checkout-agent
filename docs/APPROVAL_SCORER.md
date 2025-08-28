# ApprovalScorer Module

The ApprovalScorer module implements a two-stage approval-odds system for transaction risk assessment in the AltWallet Checkout Agent.

## Overview

The ApprovalScorer combines deterministic signals into a raw log-odds score and then calibrates it to produce an approval probability. This two-stage approach provides:

1. **Rules Layer**: Combines deterministic signals into a raw log-odds score
2. **Calibration Layer**: Maps raw scores to probabilities using configurable calibration methods

## Features

- **Deterministic Scoring**: Same inputs always produce the same outputs
- **Configurable Weights**: All feature weights are configurable via YAML
- **Pluggable Calibration**: Support for different calibration methods (logistic, isotonic)
- **Feature Attributions**: Explainable AI with detailed feature contributions
- **Robust Error Handling**: Graceful handling of missing or invalid data
- **Probability Clamping**: Configurable bounds for approval probabilities

## Input Features

The scorer considers the following features:

| Feature | Description | Type |
|---------|-------------|------|
| `mcc` | Merchant Category Code | String |
| `amount` | Transaction amount | Decimal |
| `issuer_family` | Card issuer family (visa, mastercard, etc.) | String |
| `cross_border` | Cross-border transaction flag | Boolean |
| `location_mismatch_distance` | Distance between device and geo locations | Float |
| `velocity_24h` | Number of transactions in last 24 hours | Integer |
| `velocity_7d` | Number of transactions in last 7 days | Integer |
| `chargebacks_12m` | Number of chargebacks in last 12 months | Integer |
| `merchant_risk_tier` | Merchant risk classification | String |
| `loyalty_tier` | Customer loyalty tier | String |

## Usage

### Basic Usage

```python
from decimal import Decimal
from altwallet_agent.approval_scorer import ApprovalScorer

# Initialize scorer
scorer = ApprovalScorer()

# Score a transaction
context = {
    "mcc": "5411",  # Grocery store
    "amount": Decimal("50.00"),
    "issuer_family": "visa",
    "cross_border": False,
    "location_mismatch_distance": 0.0,
    "velocity_24h": 3,
    "velocity_7d": 15,
    "chargebacks_12m": 0,
    "merchant_risk_tier": "low",
    "loyalty_tier": "GOLD"
}

result = scorer.score(context)
print(f"Approval Probability: {result.p_approval:.3f}")
print(f"Raw Score: {result.raw_score:.3f}")
```

### Feature Attributions

```python
# Get feature attributions for explainability
attributions = scorer.explain(context)
print(f"MCC contribution: {attributions.mcc_contribution:+.3f}")
print(f"Amount contribution: {attributions.amount_contribution:+.3f}")
# ... other features
```

### Custom Configuration

```python
# Use custom configuration file
scorer = ApprovalScorer("path/to/custom_config.yaml")
```

## Configuration

The scorer is configured via `config/approval.yaml`. Key configuration sections:

### Rules Layer

```yaml
rules_layer:
  # MCC-based weights
  mcc_weights:
    "7995": -2.5  # Gambling (high risk)
    "5411": 0.2   # Grocery stores (low risk)
    "default": 0.0

  # Amount-based weights
  amount_weights:
    "0-10": 0.3
    "10-50": 0.1
    "50-100": 0.0
    "100-500": -0.2
    "500-1000": -0.5
    "1000-5000": -1.0
    "5000+": -2.0

  # Other feature weights...
```

### Calibration Layer

```yaml
calibration_layer:
  method: "logistic"  # or "isotonic"
  logistic:
    bias: 0.0
    scale: 1.0
```

### Output Constraints

```yaml
output:
  min_probability: 0.01
  max_probability: 0.99
  random_seed: 42
```

## Calibration Methods

### Logistic (Platt) Calibration

The default calibration method applies a logistic transformation:

```
p_approval = 1 / (1 + exp(-(scale * raw_score + bias)))
```

### Isotonic Calibration

A placeholder for future implementation that will use learned isotonic regression parameters.

## Testing

Run the test suite:

```bash
python -m pytest tests/test_approval_scorer.py -v
```

The tests cover:
- Typical transaction scenarios
- Edge cases and missing data
- Deterministic behavior
- Feature attribution accuracy
- Configuration loading
- Error handling

## Demo

Run the demo script to see the scorer in action:

```bash
python examples/approval_demo.py
```

The demo shows:
- Low-risk transaction scoring
- High-risk transaction scoring
- Feature attributions
- Deterministic behavior verification

## Integration

The ApprovalScorer can be integrated into the existing AltWallet Checkout Agent:

```python
from altwallet_agent.approval_scorer import ApprovalScorer
from altwallet_agent.models import Context

def process_transaction(context: Context):
    # Convert Context to dict format
    context_dict = {
        "mcc": context.merchant.mcc,
        "amount": context.cart.total,
        "issuer_family": context.payment_method.issuer_family,
        # ... other fields
    }
    
    # Get approval odds
    scorer = ApprovalScorer()
    result = scorer.score(context_dict)
    
    return result.p_approval > 0.5  # Approve if > 50%
```

## Performance

- **Deterministic**: Same inputs always produce same outputs
- **Fast**: O(1) scoring complexity
- **Memory Efficient**: Minimal memory footprint
- **Thread Safe**: Can be used in multi-threaded environments

## Future Enhancements

- [ ] Implement full isotonic calibration
- [ ] Add support for time-based feature decay
- [ ] Integrate with machine learning models
- [ ] Add support for ensemble methods
- [ ] Implement online learning capabilities
