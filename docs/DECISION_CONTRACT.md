# Decision Contract Documentation

## Overview

The AltWallet Checkout Agent decision contract provides a standardized, JSON-serializable output that encapsulates transaction decisions, applied business rules, and routing hints. This contract ensures consistency across CLI, API, and logging interfaces while providing comprehensive information for downstream processing.

## Contract Structure

### Core Decision Contract

```python
from altwallet_agent.decisioning import DecisionContract

contract = DecisionContract(
    request_id="req_123",
    decision=Decision.APPROVE,
    actions=[...],
    reasons=[...],
    routing_hint=RoutingHint(...),
    confidence_score=0.95,
    timestamp="2024-01-15T10:30:00Z"
)
```

### Contract Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `request_id` | string | Yes | Unique request identifier |
| `decision` | Decision | Yes | Transaction decision (APPROVE/REVIEW/DECLINE) |
| `actions` | List[BusinessRule] | Yes | Applied business rules |
| `reasons` | List[string] | Yes | Features/flags contributing to decision |
| `routing_hint` | RoutingHint | Yes | Routing optimization information |
| `confidence_score` | float | Yes | Decision confidence (0.0-1.0) |
| `timestamp` | string | Yes | ISO 8601 timestamp |

## Decision Types

### Decision Enum

```python
from enum import Enum

class Decision(Enum):
    APPROVE = "APPROVE"      # Transaction approved
    REVIEW = "REVIEW"        # Transaction requires manual review
    DECLINE = "DECLINE"      # Transaction declined
```

### Decision Logic

| Decision | Criteria | Typical Actions |
|----------|----------|-----------------|
| `APPROVE` | Score ≥ 70, Low risk | Standard processing, loyalty boost |
| `REVIEW` | Score 50-69, Medium risk | KYC required, additional verification |
| `DECLINE` | Score < 50, High risk | Fraud detection, compliance flags |

## Business Rules

### Business Rule Structure

```python
from altwallet_agent.decisioning import BusinessRule, BusinessRuleType

rule = BusinessRule(
    rule_type=BusinessRuleType.KYC_REQUIRED,
    rule_id="kyc_001",
    description="Customer verification required for high-value transaction",
    impact="NEGATIVE",
    confidence=0.85
)
```

### Business Rule Types

| Rule Type | Description | Impact | Use Case |
|-----------|-------------|--------|----------|
| `KYC_REQUIRED` | Know Your Customer verification | NEGATIVE | High-value transactions |
| `LOYALTY_BOOST` | Loyalty program enhancement | POSITIVE | Repeat customers |
| `RISK_THRESHOLD` | Risk score threshold exceeded | NEGATIVE | Suspicious activity |
| `COMPLIANCE_CHECK` | Regulatory compliance requirement | NEGATIVE | Geographic restrictions |
| `FRAUD_DETECTION` | Fraud detection algorithm flag | NEGATIVE | Suspicious patterns |
| `NETWORK_PREFERENCE` | Network routing optimization | NEUTRAL | Cost optimization |
| `ACQUIRER_OPTIMIZATION` | Acquirer selection optimization | NEUTRAL | Success rate optimization |

### Rule Impact Classification

| Impact | Description | Example |
|---------|-------------|---------|
| `POSITIVE` | Enhances approval likelihood | Loyalty boost, good history |
| `NEGATIVE` | Reduces approval likelihood | KYC required, fraud flag |
| `NEUTRAL` | No direct impact on decision | Routing optimization |

## Routing Hints

### Routing Hint Structure

```python
from altwallet_agent.decisioning import RoutingHint, PenaltyOrIncentive

routing_hint = RoutingHint(
    preferred_network="visa",
    preferred_acquirer="stripe",
    penalty_or_incentive=PenaltyOrIncentive.SURCHARGE,
    approval_odds=0.85,
    network_preferences=["visa", "mastercard"],
    mcc_based_hint="retail_general",
    confidence=0.90
)
```

### Routing Hint Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `preferred_network` | string | Yes | "any" | Preferred payment network |
| `preferred_acquirer` | string | No | null | Preferred acquiring bank |
| `penalty_or_incentive` | PenaltyOrIncentive | Yes | - | Surcharge/suppression/none |
| `approval_odds` | float | No | null | Calculated approval probability |
| `network_preferences` | List[string] | Yes | - | Ordered network preferences |
| `mcc_based_hint` | string | No | null | MCC-based routing suggestion |
| `confidence` | float | Yes | 0.8 | Routing confidence score |

### Penalty/Incentive Types

| Type | Description | Business Impact |
|-------|-------------|-----------------|
| `surcharge` | Additional fee applied | Revenue increase, cost offset |
| `suppression` | Fee reduction or waiver | Customer retention, competitive pricing |
| `none` | Standard processing | No additional cost or benefit |

## Decision Engine

### Core Decision Logic

```python
from altwallet_agent.decisioning import DecisionEngine

engine = DecisionEngine()

# Make decision with context
contract = await engine.make_decision(context)
```

### Decision Flow

1. **Context Analysis**: Evaluate transaction context and risk factors
2. **Scoring Integration**: Integrate with existing scoring system
3. **Business Rule Application**: Apply relevant business rules
4. **Routing Hint Calculation**: Determine optimal routing strategy
5. **Confidence Assessment**: Calculate decision confidence
6. **Contract Generation**: Create standardized decision contract

### Scoring Integration

The decision engine integrates with the existing scoring system:

```python
# Get scoring result
score_result = await score_transaction(context)

# Use scoring data for decisioning
final_score = score_result.final_score
risk_score = score_result.risk_score
loyalty_boost = score_result.loyalty_boost
```

## Usage Examples

### Basic Decision Request

```python
from altwallet_agent.decisioning import DecisionEngine
from altwallet_agent.models import Context

# Create transaction context
context = Context(
    customer_id="cust_123",
    merchant_id="merch_456",
    transaction_amount=150.00,
    mcc_code="5411",
    geographic_region="US",
    device_fingerprint="device_789",
    ip_address="192.168.1.1"
)

# Make decision
engine = DecisionEngine()
contract = await engine.make_decision(context)

print(f"Decision: {contract.decision}")
print(f"Confidence: {contract.confidence_score}")
print(f"Actions: {len(contract.actions)}")
```

### Decision Contract Serialization

```python
import json

# Convert to JSON
contract_json = contract.model_dump_json(indent=2)

# Save to file
with open("decision_contract.json", "w") as f:
    f.write(contract_json)

# Load from JSON
loaded_contract = DecisionContract.model_validate_json(contract_json)
```

### Business Rule Analysis

```python
# Analyze applied rules
positive_rules = [rule for rule in contract.actions if rule.impact == "POSITIVE"]
negative_rules = [rule for rule in contract.actions if rule.impact == "NEGATIVE"]

print(f"Positive rules: {len(positive_rules)}")
print(f"Negative rules: {len(negative_rules)}")

# Check for specific rule types
kyc_rules = [rule for rule in contract.actions if rule.rule_type == BusinessRuleType.KYC_REQUIRED]
if kyc_rules:
    print("KYC verification required")
```

### Routing Hint Analysis

```python
routing = contract.routing_hint

print(f"Preferred network: {routing.preferred_network}")
print(f"Approval odds: {routing.approval_odds}")
print(f"Penalty/Incentive: {routing.penalty_or_incentive}")

if routing.penalty_or_incentive == PenaltyOrIncentive.SURCHARGE:
    print("Surcharge will be applied")
elif routing.penalty_or_incentive == PenaltyOrIncentive.SUPPRESSION:
    print("Fee suppression applied")
```

## Integration Patterns

### API Integration

```python
from fastapi import FastAPI
from altwallet_agent.decisioning import DecisionEngine

app = FastAPI()
engine = DecisionEngine()

@app.post("/decision")
async def make_decision(request: DecisionRequest):
    contract = await engine.make_decision(request.context)
    return contract
```

### CLI Integration

```python
import click
from altwallet_agent.decisioning import DecisionEngine

@click.command()
@click.option('--context-file', required=True, help='Context JSON file')
def decision_cli(context_file):
    """Make transaction decision from context file"""
    with open(context_file) as f:
        context_data = json.load(f)
    
    context = Context(**context_data)
    engine = DecisionEngine()
    contract = await engine.make_decision(context)
    
    click.echo(contract.model_dump_json(indent=2))
```

### Logging Integration

```python
from altwallet_agent.logger import get_logger

logger = get_logger()

# Log decision contract
logger.info(
    "Transaction decision made",
    request_id=contract.request_id,
    decision=contract.decision,
    confidence=contract.confidence_score,
    actions_count=len(contract.actions),
    routing_network=contract.routing_hint.preferred_network
)
```

## Validation and Error Handling

### Contract Validation

```python
from pydantic import ValidationError

try:
    contract = DecisionContract(**data)
except ValidationError as e:
    print(f"Validation error: {e}")
    # Handle validation failure
```

### Required Field Validation

The decision contract enforces required fields:

- `request_id`: Must be non-empty string
- `decision`: Must be valid Decision enum value
- `actions`: Must be non-empty list of BusinessRule objects
- `reasons`: Must be non-empty list of strings
- `routing_hint`: Must be valid RoutingHint object
- `confidence_score`: Must be float between 0.0 and 1.0
- `timestamp`: Must be valid ISO 8601 timestamp

### Business Rule Validation

```python
# Validate business rule
rule = BusinessRule(
    rule_type=BusinessRuleType.KYC_REQUIRED,
    rule_id="kyc_001",
    description="Customer verification required",
    impact="NEGATIVE",
    confidence=0.85
)

# Validate rule confidence
if rule.confidence < 0.5:
    print("Warning: Low confidence rule")
```

## Performance Considerations

### Async Processing

- Decision engine supports async operations
- Non-blocking business rule evaluation
- Concurrent routing hint calculation
- Efficient context analysis

### Caching

- Business rule definitions cached
- Routing hint calculations cached
- Context analysis results cached
- Decision contract templates cached

## Monitoring and Analytics

### Decision Metrics

Key metrics to track:
- Decision distribution (approve/review/decline)
- Average confidence scores
- Business rule application frequency
- Routing hint effectiveness
- Decision latency

### Structured Logging

```python
logger.info(
    "Decision contract generated",
    contract_id=contract.request_id,
    decision=contract.decision,
    confidence_score=contract.confidence_score,
    actions_count=len(contract.actions),
    routing_confidence=contract.routing_hint.confidence,
    processing_time_ms=latency_ms
)
```

## Best Practices

### Contract Design

1. **Consistent Structure**: Maintain consistent field ordering
2. **Clear Naming**: Use descriptive field names
3. **Type Safety**: Leverage Pydantic for validation
4. **Extensibility**: Design for future field additions

### Business Rules

1. **Rule Granularity**: Create specific, focused rules
2. **Impact Classification**: Accurately classify rule impacts
3. **Confidence Scoring**: Provide realistic confidence values
4. **Rule Documentation**: Document rule purpose and logic

### Routing Hints

1. **Network Preferences**: Order by success rate and cost
2. **Acquirer Selection**: Consider success rates and fees
3. **Penalty/Incentive Logic**: Balance revenue and customer experience
4. **Confidence Assessment**: Reflect uncertainty in routing decisions

## Troubleshooting

### Common Issues

1. **Validation Errors**
   - Check required field values
   - Verify enum value validity
   - Ensure proper data types

2. **Business Rule Failures**
   - Validate rule configuration
   - Check rule dependencies
   - Verify rule logic

3. **Routing Hint Issues**
   - Validate network preferences
   - Check acquirer configuration
   - Verify penalty/incentive logic

### Debug Commands

```python
# Validate contract structure
print(contract.model_dump_json(indent=2))

# Check business rules
for rule in contract.actions:
    print(f"Rule: {rule.rule_type}, Impact: {rule.impact}, Confidence: {rule.confidence}")

# Analyze routing hints
routing = contract.routing_hint
print(f"Network: {routing.preferred_network}, Confidence: {routing.confidence}")
```

## API Reference

### DecisionEngine Methods

- `make_decision(context: Context) -> DecisionContract`
- `_calculate_routing_hint(context: Context, score_result: ScoreResult) -> RoutingHint`
- `_determine_preferred_acquirer(context: Context, score_result: ScoreResult) -> Optional[str]`
- `_calculate_penalty_or_incentive(context: Context, score_result: ScoreResult) -> PenaltyOrIncentive`
- `_calculate_approval_odds(final_score: int) -> float`
- `_get_mcc_based_hint(mcc_code: str) -> Optional[str]`
- `_calculate_routing_confidence(context: Context, score_result: ScoreResult) -> float`

### DecisionContract Properties

- `request_id: str`
- `decision: Decision`
- `actions: List[BusinessRule]`
- `reasons: List[str]`
- `routing_hint: RoutingHint`
- `confidence_score: float`
- `timestamp: str`

### BusinessRule Properties

- `rule_type: BusinessRuleType`
- `rule_id: str`
- `description: str`
- `impact: str`
- `confidence: float`

### RoutingHint Properties

- `preferred_network: str`
- `preferred_acquirer: Optional[str]`
- `penalty_or_incentive: PenaltyOrIncentive`
- `approval_odds: Optional[float]`
- `network_preferences: List[str]`
- `mcc_based_hint: Optional[str]`
- `confidence: float`

## Version History

- **v0.3.0**: Initial decision contract implementation
  - Standardized decision output
  - Business rule integration
  - Routing hint calculation
  - Confidence scoring
  - JSON serialization support
  - Pydantic validation
