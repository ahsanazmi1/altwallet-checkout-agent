# Merchant Penalty Module

The Merchant Penalty Module calculates deterministic penalties based on merchant preferences and network requirements. These penalties are applied when merchant preferences don't align with card capabilities, helping to optimize card recommendations.

## Overview

The module provides intelligent penalty calculations by considering:

- **Merchant-Specific Penalties**: Exact merchant name + MCC combinations
- **Fuzzy Matching**: Intelligent matching for merchant name variations
- **MCC Family Fallback**: Category-based penalties when no exact merchant match
- **Network Preferences**: Penalties based on payment network requirements
- **Deterministic Results**: Consistent penalties for the same merchant/context

## Configuration

The module uses a YAML configuration file (`config/merchant_penalties.yaml`) with the following sections:

### Merchant-Specific Penalties

```yaml
merchants:
  "amazon.com":
    "5999": 0.85  # Online retail penalty
    "default": 0.90
  
  "walmart.com":
    "5311": 0.88  # Department store penalty
    "5411": 0.88  # Grocery penalty
    "default": 0.92
  
  "costco.com":
    "5411": 0.82  # Warehouse club penalty
    "default": 0.85
```

### MCC Family Penalties

```yaml
mcc_families:
  "4511": 0.90  # Airlines
  "5411": 0.95  # Grocery stores
  "5541": 0.92  # Gas stations
  "5812": 0.98  # Restaurants
  "5999": 0.94  # Online retail
  "default": 1.0
```

### Network Preference Penalties

```yaml
network_penalties:
  debit_preference: 0.85
  visa_preference: 0.90
  mastercard_preference: 0.90
  amex_preference: 0.80
  discover_preference: 0.85
  no_amex: 0.75
  no_visa: 0.70
  no_mastercard: 0.70
```

### Fuzzy Matching Configuration

```yaml
fuzzy_matching:
  similarity_threshold: 0.8
  variations:
    "amazon":
      - "amazon.com"
      - "amzn"
      - "amazon-"
    "walmart":
      - "walmart.com"
      - "walmart-"
      - "walmart"
```

## Usage

### Basic Usage

```python
from altwallet_agent.merchant_penalty import MerchantPenalty
from altwallet_agent.models import Context, Customer, Merchant, Cart, CartItem, Device, Geo, LoyaltyTier
from decimal import Decimal

# Initialize the penalty module
penalty = MerchantPenalty()

# Create a transaction context
context = Context(
    customer=Customer(
        id="customer_123",
        loyalty_tier=LoyaltyTier.GOLD,
        historical_velocity_24h=2,
        chargebacks_12m=0,
    ),
    merchant=Merchant(
        name="Amazon.com",
        mcc="5999",
        network_preferences=["visa", "mastercard"],
        location={"city": "Seattle", "country": "US"},
    ),
    cart=Cart(
        items=[
            CartItem(
                item="Online Purchase",
                unit_price=Decimal("100.00"),
                qty=1,
                mcc="5999",
                merchant_category="Online Retail",
            )
        ],
        currency="USD",
    ),
    device=Device(
        ip="192.168.1.1",
        device_id="device_123",
        ip_distance_km=5.0,
        location={"city": "Seattle", "country": "US"},
    ),
    geo=Geo(
        city="Seattle",
        region="WA",
        country="US",
        lat=47.6062,
        lon=-122.3321,
    ),
)

# Calculate merchant penalty
penalty_value = penalty.merchant_penalty(context)
print(f"Merchant penalty: {penalty_value:.3f}")
```

### Custom Configuration

```python
# Use a custom configuration file
penalty = MerchantPenalty("path/to/custom_merchant_penalties.yaml")

# Or modify configuration programmatically
penalty.config["merchants"]["new_merchant.com"] = {
    "5411": 0.88,
    "default": 0.92,
}
```

## Penalty Calculation

The final penalty is calculated using a weighted average of multiple factors:

1. **Merchant-Specific Penalty** (40%): Exact merchant name + MCC match
2. **MCC Family Penalty** (30%): Category-based fallback
3. **Network Preference Penalty** (30%): Payment network requirements

The result is bounded between the configured minimum and maximum penalties (default: 0.8 to 1.0).

## Examples

### Exact Merchant Match

```python
# Amazon.com with online retail MCC
context.merchant.name = "amazon.com"
context.merchant.mcc = "5999"
penalty_value = penalty.merchant_penalty(context)
# Result: ~0.85 (exact match penalty)
```

### Fuzzy Merchant Match

```python
# "amazon" should match "amazon.com"
context.merchant.name = "amazon"
context.merchant.mcc = "5999"
penalty_value = penalty.merchant_penalty(context)
# Result: ~0.85 (fuzzy match to amazon.com)
```

### MCC Family Fallback

```python
# Unknown merchant but known MCC
context.merchant.name = "unknown_airline"
context.merchant.mcc = "4511"  # Airlines
penalty_value = penalty.merchant_penalty(context)
# Result: ~0.90 (MCC family penalty for airlines)
```

### Network Preference

```python
# Merchant prefers debit
context.merchant.network_preferences = ["debit"]
penalty_value = penalty.merchant_penalty(context)
# Result: ~0.85 (debit preference penalty)
```

### No Data Fallback

```python
# Completely unknown merchant and MCC
context.merchant.name = "completely_unknown"
context.merchant.mcc = "9999"
context.merchant.network_preferences = []
penalty_value = penalty.merchant_penalty(context)
# Result: 1.0 (base penalty, no penalty applied)
```

## Integration

The merchant penalty module integrates with the existing scoring system:

```python
from altwallet_agent.scoring import calculate_score
from altwallet_agent.merchant_penalty import MerchantPenalty

# Calculate base score
score_result = calculate_score(context)

# Apply merchant penalty
penalty = MerchantPenalty()
merchant_penalty = penalty.merchant_penalty(context)

# Adjust final score
adjusted_score = score_result.final_score * merchant_penalty
```

## Testing

Run the test suite:

```bash
python -m pytest tests/test_merchant_penalty.py -v
```

Run the demo:

```bash
python examples/merchant_penalty_demo.py
```

## Configuration Reference

### Merchant Penalties

Common merchant penalties and their typical values:

| Merchant | MCC | Penalty | Description |
|----------|-----|---------|-------------|
| amazon.com | 5999 | 0.85 | Online retail preference |
| walmart.com | 5311 | 0.88 | Department store preference |
| costco.com | 5411 | 0.82 | Warehouse club preference |
| delta.com | 4511 | 0.88 | Airline preference |
| united.com | 4511 | 0.87 | Airline preference |

### MCC Family Penalties

| MCC | Category | Penalty | Description |
|-----|----------|---------|-------------|
| 4511 | Airlines | 0.90 | Network preferences |
| 5411 | Grocery | 0.95 | Some prefer debit |
| 5541 | Gas | 0.92 | Often prefer debit |
| 5812 | Restaurants | 0.98 | Generally accept all |
| 5999 | Online Retail | 0.94 | Network preferences |

### Network Preference Penalties

| Preference | Penalty | Description |
|------------|---------|-------------|
| debit | 0.85 | Prefers debit cards |
| visa | 0.90 | Prefers Visa |
| mastercard | 0.90 | Prefers Mastercard |
| amex | 0.80 | Prefers American Express |
| no_amex | 0.75 | Doesn't accept Amex |
| no_visa | 0.70 | Doesn't accept Visa |

## Troubleshooting

### Common Issues

1. **Configuration file not found**: The module will use default configuration if the file is missing
2. **Invalid YAML**: Check the configuration file syntax
3. **Missing required fields**: Ensure all required Context fields are provided
4. **Penalty out of bounds**: Penalties are automatically clamped to the configured range

### Debug Logging

Enable debug logging to see detailed penalty calculations:

```python
import logging
logging.getLogger("altwallet_agent.merchant_penalty").setLevel(logging.DEBUG)
```

## Future Enhancements

- Machine learning-based penalty learning
- Real-time merchant preference updates
- Dynamic penalty adjustment based on transaction history
- Integration with external merchant databases
- Geographic penalty variations


