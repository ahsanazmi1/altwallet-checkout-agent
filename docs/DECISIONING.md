# Decisioning Module

The Decisioning Module provides a standardized contract for transaction decisions that can be returned consistently across CLI, API, and logs.

## Overview

The decisioning module integrates with the existing scoring system to make final transaction decisions and provides a structured output with:

- **Decision**: The final transaction decision (APPROVE, REVIEW, DECLINE)
- **Actions**: List of applied business rules (KYC, discounts, loyalty adjustments, etc.)
- **Reasons**: List of features/flags contributing to the decision

## Key Components

### Decision Enum

```python
from altwallet_agent.decisioning import Decision

# Three possible decisions
Decision.APPROVE    # Transaction approved
Decision.REVIEW     # Transaction requires manual review
Decision.DECLINE    # Transaction declined
```

### Action Types

```python
from altwallet_agent.decisioning import ActionType

# Risk mitigation actions
ActionType.KYC_REQUIRED              # KYC verification required
ActionType.ADDITIONAL_VERIFICATION   # Additional verification needed
ActionType.MANUAL_REVIEW            # Manual review recommended

# Loyalty and rewards actions
ActionType.LOYALTY_BOOST            # Loyalty tier boost applied
ActionType.LOYALTY_ADJUSTMENT       # Loyalty adjustment made

# Discount and pricing actions
ActionType.DISCOUNT_APPLIED         # Discount applied to transaction
ActionType.SURCHARGE_APPLIED        # Surcharge applied to transaction

# Network routing actions
ActionType.NETWORK_ROUTING          # Payment network routing preference

# Fraud prevention actions
ActionType.FRAUD_SCREENING          # Fraud screening applied
ActionType.VELOCITY_LIMIT           # Velocity limit enforced
```

### Business Rule

```python
from altwallet_agent.decisioning import BusinessRule

rule = BusinessRule(
    rule_id="LOC_001",
    action_type=ActionType.ADDITIONAL_VERIFICATION,
    description="Location mismatch detected - additional verification required",
    parameters={
        "device_location": {"city": "LA", "country": "USA"},
        "transaction_location": {"city": "NYC", "country": "USA"}
    },
    impact_score=30.0
)
```

### Decision Reason

```python
from altwallet_agent.decisioning import DecisionReason

reason = DecisionReason(
    feature_name="location_mismatch",
    value=True,
    threshold=False,
    weight=0.3,
    description="Device location differs from transaction location"
)
```

### Decision Contract

The main output structure that combines all decision information:

```python
from altwallet_agent.decisioning import DecisionContract

contract = DecisionContract(
    decision=Decision.REVIEW,
    actions=[business_rule1, business_rule2],
    reasons=[reason1, reason2],
    transaction_id="txn_12345",
    confidence=0.85
)

# Convenience properties
contract.is_approved      # False
contract.requires_review  # True
contract.is_declined      # False

# Serialization methods
json_str = contract.to_json()
contract_dict = contract.to_dict()
```

## Usage

### Basic Usage

```python
from altwallet_agent.decisioning import make_transaction_decision
from altwallet_agent.models import Context

# Create transaction context
context = Context(...)

# Make decision
decision = make_transaction_decision(context, "txn_12345")

print(f"Decision: {decision.decision.value}")
print(f"Confidence: {decision.confidence:.2f}")
print(f"Actions: {len(decision.actions)}")
print(f"Reasons: {len(decision.reasons)}")
```

### Using Decision Engine

```python
from altwallet_agent.decisioning import DecisionEngine

engine = DecisionEngine()

# Make decision with custom thresholds
decision = engine.make_decision(context, "txn_12345")

# Access scoring result
score = decision.score_result.final_score
risk_score = decision.score_result.risk_score
loyalty_boost = decision.score_result.loyalty_boost
```

### Decision Thresholds

The decision engine uses these default thresholds:

- **APPROVE**: Score >= 70
- **REVIEW**: Score >= 40 and < 70
- **DECLINE**: Score < 40

These can be customized by modifying the `DecisionEngine` class.

## Business Rules

The decisioning module automatically applies business rules based on:

### Location Mismatch
- **Trigger**: Device location differs from transaction location
- **Action**: `ADDITIONAL_VERIFICATION`
- **Impact**: +30 risk score points

### High Velocity
- **Trigger**: Customer has >10 transactions in 24 hours
- **Action**: `VELOCITY_LIMIT`
- **Impact**: +20 risk score points

### Chargebacks
- **Trigger**: Customer has chargeback history
- **Action**: `KYC_REQUIRED`
- **Impact**: +25 risk score points

### High Ticket Amount
- **Trigger**: Transaction amount >= $500
- **Action**: `MANUAL_REVIEW`
- **Impact**: +10 risk score points

### Loyalty Boost
- **Trigger**: Customer has loyalty tier
- **Action**: `LOYALTY_BOOST`
- **Impact**: Positive score adjustment

### Network Routing
- **Trigger**: Merchant has network preferences
- **Action**: `NETWORK_ROUTING`
- **Impact**: Routing preference applied

## Integration Points

### CLI Integration

```python
# In CLI command
decision = make_transaction_decision(context, transaction_id)

# Output structured result
print(json.dumps(decision.to_dict(), indent=2))
```

### API Integration

```python
# In API endpoint
decision = make_transaction_decision(context, transaction_id)

# Return JSON response
return decision.to_dict()
```

### Logging Integration

```python
# In logging
decision = make_transaction_decision(context, transaction_id)

logger.info(
    "Transaction decision made",
    decision=decision.decision.value,
    confidence=decision.confidence,
    actions_count=len(decision.actions),
    reasons_count=len(decision.reasons)
)
```

## Confidence Calculation

The decision confidence is calculated based on:

- **Base confidence**: 0.8 (80%)
- **High confidence**: +0.15 for scores ≥90 or ≤20
- **Low confidence**: -0.2 for scores near thresholds (35-45, 65-75)
- **Data quality**: -0.1 for missing location data
- **Bounds**: Clamped to [0.0, 1.0]

## Testing

Run the decisioning module tests:

```bash
# Run all tests
pytest tests/test_decisioning.py

# Run specific test class
pytest tests/test_decisioning.py::TestDecisionEngine

# Run with coverage
pytest tests/test_decisioning.py --cov=src/altwallet_agent/decisioning
```

## Demo

Run the decisioning demo script:

```bash
cd examples
python decisioning_demo.py
```

This will demonstrate:
- Normal transaction processing
- Risky transaction handling
- JSON serialization
- Dictionary conversion
- Convenience functions

## Configuration

### Environment Variables

- `LOG_LEVEL`: Set logging level (default: INFO)
- `LOG_SILENT`: Set to "1" to silence logs during tests

### Customization

To customize decision thresholds or business rules:

```python
class CustomDecisionEngine(DecisionEngine):
    def __init__(self):
        super().__init__()
        self.approve_threshold = 80  # Custom approve threshold
        self.review_threshold = 50   # Custom review threshold
```

## Error Handling

The decisioning module handles errors gracefully:

- **Invalid context**: Raises validation errors
- **Scoring failures**: Logs errors and continues
- **Missing data**: Applies defaults and continues
- **Serialization errors**: Logs warnings and continues

## Performance

- **Decision time**: Typically <10ms for most transactions
- **Memory usage**: Minimal overhead (~1KB per decision)
- **Scalability**: Stateless design supports high concurrency
- **Caching**: No built-in caching (stateless by design)

## Future Enhancements

Planned improvements:

- **Machine learning integration**: Dynamic threshold adjustment
- **Real-time rule updates**: Hot-swappable business rules
- **Advanced confidence models**: Multi-factor confidence calculation
- **Audit trail**: Complete decision history tracking
- **Rule engine**: Configurable rule evaluation engine

