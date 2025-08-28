# Additive Feature Attributions

This document describes the implementation of additive feature attributions on the pre-calibration scale (log-odds/raw score) for the AltWallet Checkout Agent's ApprovalScorer.

## Overview

Additive feature attributions provide explainable AI capabilities by breaking down the raw log-odds score into individual feature contributions. Each rule contributes a signed value, and the contributions must sum to the raw score within a small epsilon, ensuring mathematical consistency.

## Structure

The additive attributions return the following structure:

```json
{
  "baseline": 0.0,
  "contribs": [
    {"feature": "mcc_travel", "value": +0.42},
    {"feature": "amount", "value": -0.15},
    {"feature": "cross_border", "value": -2.50}
  ],
  "sum": -2.23
}
```

### Fields

- **baseline**: The base score contribution (from configuration)
- **contribs**: List of feature contributions, each with:
  - **feature**: Feature name (e.g., "mcc", "amount", "cross_border")
  - **value**: Contribution value (can be positive or negative)
- **sum**: Total raw score (baseline + sum of contributions)

## Implementation Details

### Models

```python
class FeatureContribution(BaseModel):
    """Individual feature contribution to the raw score."""
    feature: str = Field(..., description="Feature name")
    value: float = Field(..., description="Contribution value")

class AdditiveAttributions(BaseModel):
    """Additive feature attributions on pre-calibration scale."""
    baseline: float = Field(..., description="Baseline score contribution")
    contribs: List[FeatureContribution] = Field(..., description="List of feature contributions")
    sum: float = Field(..., description="Total raw score")
```

### Key Methods

#### `ApprovalScorer.explain(context)`

Returns additive attributions for a transaction context:

```python
scorer = ApprovalScorer()
context = {
    "mcc": "5411",
    "amount": Decimal("100.00"),
    "issuer_family": "visa",
    # ... other fields
}

attributions = scorer.explain(context)
print(f"Raw score: {attributions.sum}")
print(f"Baseline: {attributions.baseline}")
for contrib in attributions.contribs:
    print(f"{contrib.feature}: {contrib.value:+.3f}")
```

#### `ApprovalScorer._extract_top_drivers(additive_attribs, top_k=3)`

Extracts top positive and negative feature drivers:

```python
top_drivers = scorer._extract_top_drivers(attributions, top_k=3)

print("Top Positive Drivers:")
for contrib in top_drivers["top_positive"]:
    print(f"  {contrib.feature}: +{contrib.value:.3f}")

print("Top Negative Drivers:")
for contrib in top_drivers["top_negative"]:
    print(f"  {contrib.feature}: {contrib.value:.3f}")
```

## Features

### 1. Additivity Validation

Contributions must sum to the raw score within epsilon (1e-10):

```python
contrib_sum = sum(contrib.value for contrib in attributions.contribs)
total_sum = contrib_sum + attributions.baseline
assert abs(total_sum - attributions.sum) <= 1e-10
```

### 2. Zero Contribution Filtering

Features with zero contribution are excluded from the list to reduce noise.

### 3. Top Drivers Extraction

Automatically identifies the most influential positive and negative features:

```python
# For high-risk transaction
top_drivers = scorer._extract_top_drivers(attributions)
# Returns: {"top_positive": [...], "top_negative": [...]}
```

### 4. JSON Serialization

Attributions can be easily serialized for API responses:

```python
import json
json_str = json.dumps(attributions.model_dump(), indent=2)
```

## Usage Examples

### Basic Usage

```python
from altwallet_agent.approval_scorer import ApprovalScorer
from decimal import Decimal

scorer = ApprovalScorer()

# Score a transaction
context = {
    "mcc": "5411",  # Grocery store
    "amount": Decimal("50.00"),
    "issuer_family": "visa",
    "cross_border": False,
    "location_mismatch_distance": 0.0,
    "velocity_24h": 2,
    "velocity_7d": 8,
    "chargebacks_12m": 0,
    "merchant_risk_tier": "low",
    "loyalty_tier": "PLATINUM"
}

# Get approval result with additive attributions
result = scorer.score(context)
print(f"Approval Probability: {result.p_approval:.3f}")
print(f"Raw Score: {result.raw_score:.3f}")

# Get detailed attributions
attributions = result.additive_attributions
print(f"Baseline: {attributions.baseline:.3f}")
for contrib in attributions.contribs:
    sign = "+" if contrib.value >= 0 else ""
    print(f"  {contrib.feature}: {sign}{contrib.value:.3f}")
```

### Top Drivers Analysis

```python
# Extract top drivers
top_drivers = scorer._extract_top_drivers(attributions, top_k=3)

print("Key Risk Factors:")
for contrib in top_drivers["top_negative"]:
    print(f"  - {contrib.feature}: {contrib.value:.3f}")

print("Key Positive Factors:")
for contrib in top_drivers["top_positive"]:
    print(f"  - {contrib.feature}: +{contrib.value:.3f}")
```

### API Integration

```python
# For API responses
def get_approval_with_explanation(context):
    result = scorer.score(context)
    return {
        "approval_probability": result.p_approval,
        "raw_score": result.raw_score,
        "explanation": {
            "baseline": result.additive_attributions.baseline,
            "contributions": [
                {
                    "feature": contrib.feature,
                    "value": contrib.value,
                    "impact": "positive" if contrib.value > 0 else "negative"
                }
                for contrib in result.additive_attributions.contribs
            ],
            "total_score": result.additive_attributions.sum
        }
    }
```

## Benefits

1. **Transparency**: Clear breakdown of how each feature affects the score
2. **Debugging**: Easy identification of problematic features
3. **Compliance**: Meets regulatory requirements for explainable AI
4. **User Experience**: Provides meaningful explanations to users
5. **Model Validation**: Ensures mathematical consistency with additivity checks

## Testing

Comprehensive tests are included in `tests/test_additive_attributions.py`:

- Structure validation
- Additivity validation
- Top drivers extraction
- Edge cases
- JSON serialization
- High-risk vs low-risk comparison

Run tests with:

```bash
python -m pytest tests/test_additive_attributions.py -v
```

## Demo

See `examples/additive_attributions_demo.py` for a complete demonstration of the functionality.

Run the demo with:

```bash
python examples/additive_attributions_demo.py
```

## Configuration

The additive attributions work with the existing approval scorer configuration. Feature weights are defined in `config/approval.yaml` and automatically contribute to the attributions.

## Future Enhancements

1. **Feature Grouping**: Group related features for higher-level explanations
2. **Temporal Analysis**: Track attribution changes over time
3. **Comparative Analysis**: Compare attributions across similar transactions
4. **Visualization**: Generate charts and graphs from attributions
5. **Custom Metrics**: Allow custom attribution aggregation methods
