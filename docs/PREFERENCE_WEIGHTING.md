# Preference & Loyalty Weighting Module

The Preference & Loyalty Weighting Module calculates multiplicative weights for card recommendations based on user preferences, loyalty tiers, category boosts, and issuer promotions. These weights are used to adjust card scores in the range [0.5, 1.5] centered at 1.0.

## Overview

The module provides intelligent card recommendations by considering:

- **User Preferences**: Cashback vs points preference, issuer affinity, annual fee tolerance, foreign transaction fee sensitivity
- **Loyalty Tiers**: Customer loyalty level (NONE, SILVER, GOLD, PLATINUM, DIAMOND)
- **Category Boosts**: Merchant Category Code (MCC) based multipliers
- **Issuer Promotions**: Special boosts for cards with active promotions or statement credits
- **Seasonal Promotions**: Time-based boosts for special offers

## Configuration

The module uses a YAML configuration file (`config/preferences.yaml`) with the following sections:

### User Preferences

```yaml
user_preferences:
  # Cashback vs Points preference (0.0 = strongly prefer points, 1.0 = strongly prefer cashback)
  cashback_vs_points_weight: 0.5
  
  # Issuer affinity weights (positive values favor specific issuers)
  issuer_affinity:
    chase: 0.0
    american_express: 0.0
    citi: 0.0
    capital_one: 0.0
    wells_fargo: 0.0
    bank_of_america: 0.0
    discover: 0.0
    us_bank: 0.0
  
  # Annual fee tolerance (0.0 = avoid fees, 1.0 = fee-agnostic)
  annual_fee_tolerance: 0.5
  
  # Foreign transaction fee sensitivity (0.0 = very sensitive, 1.0 = not sensitive)
  foreign_fee_sensitivity: 0.7
```

### Loyalty Tier Multipliers

```yaml
loyalty_tiers:
  NONE: 1.0      # No loyalty tier - no boost
  SILVER: 1.05   # 5% boost for silver tier customers
  GOLD: 1.10     # 10% boost for gold tier customers
  PLATINUM: 1.15 # 15% boost for platinum tier customers
  DIAMOND: 1.20  # 20% boost for diamond tier customers
```

### Category Boost Multipliers

```yaml
category_boosts:
  # Travel categories
  "4511": 1.15  # Airlines
  "4722": 1.10  # Travel agencies
  "5812": 1.10  # Restaurants
  "5411": 1.08  # Grocery stores
  "5541": 1.05  # Gas stations
  "default": 1.0
```

### Issuer Promotions

```yaml
issuer_promotions:
  chase:
    freedom_flex_5x_quarterly: 1.15  # 5% back on quarterly categories
    sapphire_travel_credit: 1.10     # Travel credit benefits
  american_express:
    gold_dining_credit: 1.12         # $10/month dining credit
    platinum_airline_credit: 1.15    # $200 airline fee credit
```

### Seasonal Promotions

```yaml
seasonal_promotions:
  holiday_shopping:
    start_date: "11-01"
    end_date: "12-31"
    multiplier: 1.08
    affected_categories:
      - "5311"  # Department stores
      - "5999"  # Miscellaneous retail
```

## Usage

### Basic Usage

```python
from altwallet_agent.preference_weighting import PreferenceWeighting
from altwallet_agent.models import Context, Customer, Merchant, Cart, CartItem, Device, Geo, LoyaltyTier
from decimal import Decimal

# Initialize the weighting module
weighting = PreferenceWeighting()

# Create a transaction context
context = Context(
    customer=Customer(
        id="customer_123",
        loyalty_tier=LoyaltyTier.GOLD,
        historical_velocity_24h=2,
        chargebacks_12m=0,
    ),
    merchant=Merchant(
        name="Restaurant",
        mcc="5812",  # Restaurants
        network_preferences=["visa", "mastercard"],
        location={"city": "New York", "country": "US"},
    ),
    cart=Cart(
        items=[
            CartItem(
                item="Dinner",
                unit_price=Decimal("50.00"),
                qty=1,
                mcc="5812",
                merchant_category="Restaurant",
            )
        ],
        currency="USD",
    ),
    device=Device(
        ip="192.168.1.1",
        device_id="device_123",
        ip_distance_km=5.0,
        location={"city": "New York", "country": "US"},
    ),
    geo=Geo(
        city="New York",
        region="NY",
        country="US",
        lat=40.7128,
        lon=-74.0060,
    ),
)

# Card metadata
card = {
    "name": "Chase Sapphire Preferred",
    "issuer": "Chase",
    "annual_fee": 95,
    "rewards_type": "points",
    "signup_bonus_points": 60000,
    "category_bonuses": {
        "travel": 0.025,
        "dining": 0.025,
    },
    "travel_benefits": ["Trip cancellation insurance"],
    "foreign_transaction_fee": 0.0,
}

# Calculate preference weight
weight = weighting.preference_weight(card, context)
print(f"Preference weight: {weight:.3f}")
```

### Custom Configuration

```python
# Use a custom configuration file
weighting = PreferenceWeighting("path/to/custom_preferences.yaml")

# Or modify configuration programmatically
weighting.config["user_preferences"]["cashback_vs_points_weight"] = 0.8
weighting.config["user_preferences"]["issuer_affinity"]["chase"] = 0.2
```

## Weight Calculation

The final weight is calculated using a weighted average of multiple factors:

1. **User Preferences** (30%): Cashback vs points, issuer affinity, fee tolerance
2. **Loyalty Tier** (20%): Customer loyalty level multiplier
3. **Category Boost** (25%): MCC-based category multipliers
4. **Issuer Promotions** (15%): Active promotions and credits
5. **Base Weight** (10%): Neutral baseline

The result is bounded between the configured minimum and maximum weights (default: 0.5 to 1.5).

## Examples

### Loyalty Tier Impact

```python
# Different loyalty tiers produce different weights
for tier in [LoyaltyTier.NONE, LoyaltyTier.SILVER, LoyaltyTier.GOLD, LoyaltyTier.PLATINUM, LoyaltyTier.DIAMOND]:
    context.customer.loyalty_tier = tier
    weight = weighting.preference_weight(card, context)
    print(f"{tier.value}: {weight:.3f}")
```

Output:
```
NONE: 1.042
SILVER: 1.052
GOLD: 1.062
PLATINUM: 1.073
DIAMOND: 1.083
```

### Category Boost Impact

```python
# Different merchant categories get different boosts
categories = [
    ("5411", "Grocery Store"),
    ("5812", "Restaurant"),
    ("4511", "Airline"),
]

for mcc, name in categories:
    context.merchant.mcc = mcc
    weight = weighting.preference_weight(card, context)
    print(f"{name}: {weight:.3f}")
```

Output:
```
Grocery Store: 1.042
Restaurant: 1.061
Airline: 1.074
```

### User Preference Impact

```python
# Cashback vs points preference
weighting.config["user_preferences"]["cashback_vs_points_weight"] = 0.8  # Prefer cashback
cashback_weight = weighting.preference_weight(cashback_card, context)

weighting.config["user_preferences"]["cashback_vs_points_weight"] = 0.2  # Prefer points
points_weight = weighting.preference_weight(points_card, context)
```

## Integration

The preference weighting module integrates with the existing scoring system:

```python
from altwallet_agent.scoring import calculate_score
from altwallet_agent.preference_weighting import PreferenceWeighting

# Calculate base score
score_result = calculate_score(context)

# Apply preference weighting
weighting = PreferenceWeighting()
preference_weight = weighting.preference_weight(card, context)

# Adjust final score
adjusted_score = score_result.final_score * preference_weight
```

## Testing

Run the test suite:

```bash
python -m pytest tests/test_preference_weighting.py -v
```

Run the demo:

```bash
python examples/preference_demo.py
```

## Configuration Reference

### User Preferences

| Setting | Range | Description |
|---------|-------|-------------|
| `cashback_vs_points_weight` | 0.0 - 1.0 | 0.0 = strongly prefer points, 1.0 = strongly prefer cashback |
| `issuer_affinity.*` | -0.3 - 0.3 | Affinity for specific issuers (positive = favor, negative = disfavor) |
| `annual_fee_tolerance` | 0.0 - 1.0 | 0.0 = avoid fees, 1.0 = fee-agnostic |
| `foreign_fee_sensitivity` | 0.0 - 1.0 | 0.0 = very sensitive to foreign fees, 1.0 = not sensitive |

### Loyalty Tiers

| Tier | Multiplier | Description |
|------|------------|-------------|
| NONE | 1.0 | No loyalty tier - no boost |
| SILVER | 1.05 | 5% boost for silver tier customers |
| GOLD | 1.10 | 10% boost for gold tier customers |
| PLATINUM | 1.15 | 15% boost for platinum tier customers |
| DIAMOND | 1.20 | 20% boost for diamond tier customers |

### Category Boosts

Common MCC codes and their default multipliers:

| MCC | Category | Multiplier |
|-----|----------|------------|
| 4511 | Airlines | 1.15 |
| 4722 | Travel agencies | 1.10 |
| 5812 | Restaurants | 1.10 |
| 5411 | Grocery stores | 1.08 |
| 5541 | Gas stations | 1.05 |
| 5311 | Department stores | 1.03 |
| 5999 | Miscellaneous retail | 1.02 |

## Troubleshooting

### Common Issues

1. **Configuration file not found**: The module will use default configuration if the file is missing
2. **Invalid YAML**: Check the configuration file syntax
3. **Missing required fields**: Ensure all required Context fields are provided
4. **Weight out of bounds**: Weights are automatically clamped to the configured range

### Debug Logging

Enable debug logging to see detailed weight calculations:

```python
import logging
logging.getLogger("altwallet_agent.preference_weighting").setLevel(logging.DEBUG)
```

## Future Enhancements

- Machine learning-based preference learning
- Real-time promotion detection
- Dynamic category boost adjustment
- Personalized issuer recommendations
- Integration with external loyalty systems


