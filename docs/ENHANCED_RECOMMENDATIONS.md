# Enhanced Recommendations with Explainability and Audit

This document describes the enhanced recommendation response format that includes detailed explainability information and audit trails for the AltWallet Checkout Agent.

## Overview

The enhanced recommendations extend the basic recommendation system with:

- **Key Metrics**: `p_approval`, `expected_rewards`, `utility`
- **Explainability**: Baseline, per-feature contributions, calibration info, and top drivers
- **Audit Information**: Config versions, code version, request ID, and latency

## Response Structure

### EnhancedRecommendation Model

```python
class EnhancedRecommendation(BaseModel):
    # Core recommendation fields
    card_id: str
    card_name: str
    rank: int
    
    # Key metrics
    p_approval: float          # Approval probability (0.0-1.0)
    expected_rewards: float    # Expected rewards rate
    utility: float            # Overall utility score (0.0-1.0)
    
    # Explainability
    explainability: dict[str, Any]
    
    # Audit information
    audit: dict[str, Any]
```

### EnhancedCheckoutResponse Model

```python
class EnhancedCheckoutResponse(BaseModel):
    transaction_id: str
    recommendations: list[EnhancedRecommendation]
    score: float
    status: str
    metadata: dict[str, Any]
```

## Key Metrics

### 1. p_approval
- **Type**: `float` (0.0-1.0)
- **Description**: Probability of card approval for the transaction
- **Source**: ApprovalScorer with additive feature attributions
- **Usage**: Primary risk assessment metric

### 2. expected_rewards
- **Type**: `float` (≥0.0)
- **Description**: Expected rewards rate for the card/transaction combination
- **Source**: CompositeUtility calculation
- **Usage**: Rewards optimization metric

### 3. utility
- **Type**: `float` (0.0-1.0)
- **Description**: Overall utility score combining multiple factors
- **Source**: CompositeUtility weighted calculation
- **Usage**: Final ranking metric

## Explainability Information

### Structure

```json
{
  "explainability": {
    "baseline": 0.0,
    "contributions": [
      {
        "feature": "mcc",
        "value": 0.42,
        "impact": "positive"
      },
      {
        "feature": "amount",
        "value": -0.15,
        "impact": "negative"
      }
    ],
    "calibration": {
      "method": "logistic",
      "params": {"bias": 0.0, "scale": 1.0}
    },
    "top_drivers": {
      "positive": [
        {
          "feature": "loyalty_tier",
          "value": 0.5,
          "magnitude": 0.5
        }
      ],
      "negative": [
        {
          "feature": "cross_border",
          "value": -1.0,
          "magnitude": 1.0
        }
      ]
    }
  }
}
```

### Components

#### baseline
- Base score contribution from configuration
- Represents the neutral starting point

#### contributions
- List of all feature contributions to the score
- Each contribution includes:
  - `feature`: Feature name
  - `value`: Contribution value (positive or negative)
  - `impact`: "positive" or "negative"

#### calibration
- Calibration method and parameters used
- Ensures transparency in probability calculation

#### top_drivers
- Top 3 positive and negative feature drivers
- Ordered by magnitude (absolute value)
- Includes magnitude for easy comparison

## Audit Information

### Structure

```json
{
  "audit": {
    "config_versions": {
      "config/approval.yaml": "1703123456",
      "config/preferences.yaml": "1703123457"
    },
    "code_version": "a1b2c3d4",
    "request_id": "uuid-1234-5678-9abc-def012345678",
    "latency_ms": 150
  }
}
```

### Components

#### config_versions
- Version indicators for configuration files
- Uses file modification timestamps
- Tracks changes in approval and preferences configs

#### code_version
- Git SHA of the deployed code (first 8 characters)
- Enables code version tracking and rollback

#### request_id
- Unique UUID for each request
- Enables request tracing and debugging

#### latency_ms
- Processing time in milliseconds
- Performance monitoring and optimization

## Usage Examples

### Basic Usage

```python
from altwallet_agent.core import CheckoutAgent
from altwallet_agent.models import CheckoutRequest

agent = CheckoutAgent()

# Create request
request = CheckoutRequest(
    merchant_id="merchant_123",
    amount=Decimal("100.00"),
    currency="USD",
    # ... other fields
)

# Get enhanced recommendations
response = agent.process_checkout_enhanced(request)

# Access enhanced data
for rec in response.recommendations:
    print(f"Card: {rec.card_name}")
    print(f"Approval Probability: {rec.p_approval:.3f}")
    print(f"Expected Rewards: {rec.expected_rewards:.3f}")
    print(f"Utility Score: {rec.utility:.3f}")
    
    # Explainability
    print(f"Baseline: {rec.explainability['baseline']:.3f}")
    
    # Top drivers
    for driver in rec.explainability['top_drivers']['positive']:
        print(f"  + {driver['feature']}: +{driver['value']:.3f}")
    
    for driver in rec.explainability['top_drivers']['negative']:
        print(f"  - {driver['feature']}: {driver['value']:.3f}")
```

### API Integration

```python
# For API responses
def get_enhanced_recommendations(request_data):
    agent = CheckoutAgent()
    request = CheckoutRequest(**request_data)
    response = agent.process_checkout_enhanced(request)
    
    return {
        "transaction_id": response.transaction_id,
        "score": response.score,
        "status": response.status,
        "recommendations": [
            {
                "card_id": rec.card_id,
                "card_name": rec.card_name,
                "rank": rec.rank,
                "p_approval": rec.p_approval,
                "expected_rewards": rec.expected_rewards,
                "utility": rec.utility,
                "explainability": rec.explainability,
                "audit": rec.audit
            }
            for rec in response.recommendations
        ]
    }
```

### Compact JSON Format

For API responses, use a compact format:

```json
{
  "transaction_id": "uuid-1234",
  "score": 0.85,
  "status": "completed",
  "recommendations": [
    {
      "card_id": "chase_sapphire_reserve",
      "card_name": "Chase Sapphire Reserve",
      "rank": 1,
      "p_approval": 0.92,
      "expected_rewards": 0.045,
      "utility": 0.88,
      "explainability": {
        "baseline": 0.0,
        "contributions": [...],
        "top_drivers": {...}
      },
      "audit": {
        "request_id": "uuid-1234",
        "code_version": "a1b2c3d4",
        "latency_ms": 150
      }
    }
  ]
}
```

## Benefits

### 1. Transparency
- Clear breakdown of how each feature affects the score
- Top drivers highlight the most important factors
- Calibration information ensures probability accuracy

### 2. Debugging
- Request ID enables request tracing
- Config versions track configuration changes
- Latency monitoring for performance optimization

### 3. Compliance
- Audit trail for regulatory requirements
- Explainability for AI/ML transparency
- Version tracking for model governance

### 4. User Experience
- Meaningful explanations for recommendations
- Confidence metrics for decision making
- Performance indicators for system health

## Testing

Comprehensive tests are included in `tests/test_enhanced_recommendations.py`:

- Structure validation
- Explainability accuracy
- Audit information completeness
- JSON serialization
- Recommendation ranking

Run tests with:

```bash
python -m pytest tests/test_enhanced_recommendations.py -v
```

## Demo

See `examples/enhanced_recommendations_demo.py` for a complete demonstration.

Run the demo with:

```bash
python examples/enhanced_recommendations_demo.py
```

## Configuration

The enhanced recommendations work with existing configuration:

- `config/approval.yaml`: Approval scoring configuration
- `config/preferences.yaml`: Preference weighting configuration

Config versions are automatically tracked in audit information.

## Future Enhancements

1. **Feature Grouping**: Group related features for higher-level explanations
2. **Temporal Analysis**: Track attribution changes over time
3. **Comparative Analysis**: Compare attributions across similar transactions
4. **Visualization**: Generate charts and graphs from attributions
5. **Custom Metrics**: Allow custom attribution aggregation methods
6. **Performance Optimization**: Cache explainability calculations
7. **Real-time Monitoring**: Live dashboard for recommendation performance
