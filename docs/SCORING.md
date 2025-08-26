# AltWallet Deterministic Scoring v1

## Overview

The AltWallet Deterministic Scoring system provides transparent, rule-based risk assessment for payment transactions. The system calculates a risk score based on simple, deterministic rules and applies loyalty boosts to generate a final score.

## Architecture

### Core Components

- **`policy.py`**: Contains all scoring constants and thresholds
- **`scoring.py`**: Main scoring logic and ScoreResult model
- **`models.py`**: Data models for transaction context

### ScoreResult Model

```python
class ScoreResult(BaseModel):
    risk_score: int          # Risk score (0-100)
    loyalty_boost: int       # Loyalty boost points
    final_score: int         # Final score (0-120)
    routing_hint: str        # Payment network preference
    signals: Dict[str, Any]  # Detailed scoring signals
```

## Risk Scoring Rules

The system starts with a base risk score of 0 and applies the following rules:

### 1. Location Mismatch (+30 points)
- **Trigger**: Device location differs from transaction location
- **Logic**: Compares city and country between device and transaction geo

### 2. High Velocity (+20 points)
- **Trigger**: Customer has >10 transactions in last 24 hours
- **Logic**: `customer.historical_velocity_24h > 10`

### 3. Chargebacks (+25 points)
- **Trigger**: Customer has any chargebacks in last 12 months
- **Logic**: `customer.chargebacks_12m > 0`

### 4. High Ticket Amount (+10 points)
- **Trigger**: Cart total ≥ $500 USD
- **Logic**: `cart.total >= 500.00`

## Loyalty Boost

Loyalty tiers provide score boosts:

| Tier | Boost |
|------|-------|
| NONE | 0 |
| SILVER | +5 |
| GOLD | +10 |
| PLATINUM | +15 |

## Final Score Calculation

```
final_score = max(0, 100 - risk_score) + loyalty_boost
```

The final score is clamped to the range [0, 120].

## Routing Hints

The system determines payment network preferences in this order:

1. **Merchant Preferences**: Use first network preference if available
2. **MCC-Based**: Infer from Merchant Category Code
3. **Default**: Return "any"

### MCC to Network Mapping

| MCC | Category | Preferred Network |
|-----|----------|-------------------|
| 5541, 5542 | Gas Stations | Visa |
| 5411 | Grocery Stores | Mastercard |
| 5311 | Department Stores | Visa |
| 5732 | Electronics | Mastercard |
| 5940 | Online Retail | Visa |
| 4722 | Travel Agencies | Visa |
| 4511 | Airlines | Visa |
| 7011 | Hotels | Mastercard |
| 5812-5814 | Restaurants | Visa |

## Usage

### Basic Usage

```python
from altwallet_agent.models import Context
from altwallet_agent.scoring import score_transaction

# Create transaction context
context = Context(...)

# Score the transaction
result = score_transaction(context)

print(f"Risk Score: {result.risk_score}")
print(f"Loyalty Boost: {result.loyalty_boost}")
print(f"Final Score: {result.final_score}")
print(f"Routing Hint: {result.routing_hint}")
```

### Individual Functions

```python
from altwallet_agent.scoring import (
    calculate_risk_score,
    calculate_loyalty_boost,
    calculate_final_score,
    determine_routing_hint
)

# Calculate components separately
risk_score, signals = calculate_risk_score(context)
loyalty_boost = calculate_loyalty_boost(context.customer.loyalty_tier)
final_score = calculate_final_score(risk_score, loyalty_boost)
routing_hint = determine_routing_hint(context)
```

### Pure Functions for Testing

```python
from altwallet_agent.scoring import (
    is_location_mismatch,
    is_high_velocity,
    is_high_ticket
)

# Test individual risk factors
location_mismatch = is_location_mismatch(
    device_location={"city": "NYC", "country": "US"},
    geo_location={"city": "LA", "country": "US"}
)

high_velocity = is_high_velocity(15)  # True
high_ticket = is_high_ticket(Decimal("600.00"))  # True
```

## Examples

### Low-Risk Transaction
- Cart: $50 grocery purchase
- Customer: Silver tier, 3 transactions/24h, 0 chargebacks
- Location: Device and transaction in same city
- **Result**: Risk Score 0, Loyalty Boost +5, Final Score 105

### High-Risk Transaction
- Cart: $800 electronics purchase
- Customer: No tier, 15 transactions/24h, 2 chargebacks
- Location: Device in NYC, transaction in LA
- **Result**: Risk Score 85, Loyalty Boost 0, Final Score 15

### Premium Customer with Risk
- Cart: $600 hotel booking
- Customer: Platinum tier, 8 transactions/24h, 0 chargebacks
- Location: Same city
- **Result**: Risk Score 10, Loyalty Boost +15, Final Score 105

## Testing

Run the comprehensive test suite:

```bash
python -m pytest tests/test_scoring.py -v
```

Or run the demonstration:

```bash
python examples/scoring_demo.py
```

## Policy Configuration

All scoring constants are defined in `policy.py`:

```python
# Risk scoring constants
RISK_SCORE_LOCATION_MISMATCH = 30
RISK_SCORE_VELOCITY_FLAG = 20
RISK_SCORE_CHARGEBACKS = 25
RISK_SCORE_HIGH_TICKET = 10

# Thresholds
HIGH_TICKET_THRESHOLD = Decimal("500.00")
VELOCITY_THRESHOLD_24H = 10

# Loyalty boost values
LOYALTY_BOOST_VALUES = {
    "NONE": 0,
    "SILVER": 5,
    "GOLD": 10,
    "PLATINUM": 15,
}
```

## Signals and Debugging

The `signals` field in ScoreResult contains detailed information:

```python
{
    "location_mismatch": bool,
    "velocity_flag": bool,
    "chargebacks_present": bool,
    "high_ticket": bool,
    "risk_factors": List[str],
    "cart_total": float,
    "customer_velocity_24h": int,
    "customer_chargebacks_12m": int,
    "loyalty_tier": str,
    "merchant_mcc": str,
    "merchant_network_preferences": List[str],
    "routing_hint": str,
    "loyalty_boost": int,
    "final_score": int
}
```

## Design Principles

1. **Transparency**: All rules are explicit and deterministic
2. **Simplicity**: Easy to understand and modify
3. **Testability**: Pure functions for unit testing
4. **Extensibility**: Modular design for adding new rules
5. **Performance**: Fast, stateless calculations

## Future Enhancements

- Machine learning-based risk scoring
- Dynamic threshold adjustment
- Real-time fraud detection integration
- Multi-currency support
- Advanced routing algorithms
