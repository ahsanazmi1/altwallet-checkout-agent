# Composite Utility Module

The Composite Utility Module calculates comprehensive utility scores for card recommendations by combining multiple factors into a single optimization metric. This module enables intelligent card ranking based on the complete transaction context.

## Overview

The composite utility formula combines four key components:

```
utility = p_approval × expected_rewards × preference_weight × merchant_penalty
```

Where:
- **p_approval**: Probability of card approval (0.0 to 1.0)
- **expected_rewards**: Expected rewards multiplier (e.g., 0.05 = 5% rewards)
- **preference_weight**: User preference weight (0.5 to 1.5)
- **merchant_penalty**: Merchant-specific penalty (0.8 to 1.0)

## Key Features

- **Multi-factor Optimization**: Combines approval probability, rewards, preferences, and penalties
- **Intelligent Ranking**: Sorts cards by utility score for optimal recommendations
- **Context-Aware**: Adapts to different MCCs, loyalty tiers, and merchant preferences
- **Rank Shift Analysis**: Demonstrates how rankings change across scenarios
- **Component Breakdown**: Provides detailed analysis of each utility component

## Usage

### Basic Usage

```python
from altwallet_agent.composite_utility import CompositeUtility
from altwallet_agent.models import Context, Customer, Merchant, Cart, CartItem, Device, Geo, LoyaltyTier
from decimal import Decimal

# Initialize the utility calculator
utility = CompositeUtility()

# Create sample cards
cards = [
    {
        "card_id": "chase_sapphire_preferred",
        "name": "Chase Sapphire Preferred",
        "cashback_rate": 0.02,
        "category_bonuses": {
            "4511": 2.0,  # Airlines
            "5812": 2.0,  # Restaurants
        },
        "issuer": "chase",
        "annual_fee": 95,
        "rewards_type": "points",
    },
    {
        "card_id": "amex_gold",
        "name": "American Express Gold",
        "cashback_rate": 0.04,
        "category_bonuses": {
            "5812": 4.0,  # Restaurants
            "5411": 4.0,  # Grocery stores
        },
        "issuer": "american_express",
        "annual_fee": 250,
        "rewards_type": "points",
    },
]

# Create transaction context
context = Context(
    customer=Customer(
        id="customer_123",
        loyalty_tier=LoyaltyTier.GOLD,
        historical_velocity_24h=2,
        chargebacks_12m=0,
    ),
    merchant=Merchant(
        name="Delta Airlines",
        mcc="4511",  # Airlines
        network_preferences=["visa", "mastercard"],
        location={"city": "New York", "country": "US"},
    ),
    cart=Cart(
        items=[
            CartItem(
                item="Flight Ticket",
                unit_price=Decimal("500.00"),
                qty=1,
                mcc="4511",
                merchant_category="Airlines",
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

# Calculate utility for a single card
card_utility = utility.calculate_card_utility(cards[0], context)
print(f"Utility Score: {card_utility['utility_score']:.4f}")
print(f"P(Approval): {card_utility['components']['p_approval']:.3f}")
print(f"Expected Rewards: {card_utility['components']['expected_rewards']:.3f}")
print(f"Preference Weight: {card_utility['components']['preference_weight']:.3f}")
print(f"Merchant Penalty: {card_utility['components']['merchant_penalty']:.3f}")

# Rank all cards by utility
ranked_cards = utility.rank_cards_by_utility(cards, context)
for i, card in enumerate(ranked_cards):
    print(f"{i+1}. {card['card_name']}: {card['utility_score']:.4f}")
```

### Rank Shift Analysis

The module demonstrates how card rankings change across different scenarios:

#### Travel vs Grocery MCCs

```python
# Travel scenario (airlines)
travel_context = create_context(mcc="4511", merchant_name="Delta Airlines")
travel_ranked = utility.rank_cards_by_utility(cards, travel_context)
print(f"Travel top: {travel_ranked[0]['card_name']}")

# Grocery scenario
grocery_context = create_context(mcc="5411", merchant_name="Whole Foods")
grocery_ranked = utility.rank_cards_by_utility(cards, grocery_context)
print(f"Grocery top: {grocery_ranked[0]['card_name']}")
```

**Expected Result**: Chase Sapphire Preferred for travel, American Express Gold for grocery

#### Loyalty Tier Effects

```python
# GOLD loyalty tier
gold_context = create_context(loyalty_tier=LoyaltyTier.GOLD)
gold_ranked = utility.rank_cards_by_utility(cards, gold_context)

# NONE loyalty tier
none_context = create_context(loyalty_tier=LoyaltyTier.NONE)
none_ranked = utility.rank_cards_by_utility(cards, none_context)
```

**Expected Result**: Premium cards favored for higher loyalty tiers

#### Merchant Preferences

```python
# Debit preference
debit_context = create_context(network_preferences=["debit"])
debit_ranked = utility.rank_cards_by_utility(cards, debit_context)

# No preference
no_pref_context = create_context(network_preferences=[])
no_pref_ranked = utility.rank_cards_by_utility(cards, no_pref_context)
```

**Expected Result**: Debit-friendly cards favored when merchant prefers debit

## Component Details

### Approval Probability (p_approval)

Converts scoring system scores to approval probabilities:

| Score Range | Normalized | Probability | Description |
|-------------|------------|-------------|-------------|
| 96-120 | 0.8-1.0 | 0.95 | Very high approval |
| 72-95 | 0.6-0.8 | 0.85 | High approval |
| 48-71 | 0.4-0.6 | 0.70 | Medium approval |
| 24-47 | 0.2-0.4 | 0.50 | Low approval |
| 0-23 | 0.0-0.2 | 0.25 | Very low approval |

### Expected Rewards

Calculates total expected rewards including:
- Base cashback/points rate
- Category bonuses (MCC-based multipliers)
- Signup bonuses (if eligible)
- Capped at 10% maximum

### Preference Weight

Uses the Preference & Loyalty Weighting module to calculate:
- User preference adjustments (cashback vs points, issuer affinity)
- Loyalty tier multipliers
- Category boost effects
- Seasonal promotions

### Merchant Penalty

Uses the Merchant Penalty module to calculate:
- Merchant-specific penalties
- MCC family fallbacks
- Network preference penalties
- Fuzzy merchant matching

## Utility Analysis

The module provides comprehensive analysis of utility components:

```python
analysis = utility.analyze_utility_components(cards, context)

print(f"Total cards: {analysis['total_cards']}")
print(f"Top card: {analysis['top_card']}")
print(f"Top utility: {analysis['top_utility']:.4f}")

print("Utility Range:")
print(f"  Min: {analysis['utility_range']['min']:.4f}")
print(f"  Max: {analysis['utility_range']['max']:.4f}")
print(f"  Avg: {analysis['utility_range']['avg']:.4f}")

print("Component Ranges:")
for component, ranges in analysis['component_ranges'].items():
    print(f"  {component}: {ranges['min']:.3f} - {ranges['max']:.3f}")
```

## Integration

The composite utility module integrates with the existing scoring system:

```python
from altwallet_agent.scoring import score_transaction
from altwallet_agent.preference_weighting import PreferenceWeighting
from altwallet_agent.merchant_penalty import MerchantPenalty
from altwallet_agent.composite_utility import CompositeUtility

# Calculate base score
score_result = score_transaction(context)

# Calculate utility
utility = CompositeUtility()
ranked_cards = utility.rank_cards_by_utility(cards, context)

# Use top-ranked card
top_card = ranked_cards[0]
print(f"Recommended: {top_card['card_name']}")
```

## Testing

Run the test suite:

```bash
python -m pytest tests/test_composite_utility.py -v
```

Run the demo:

```bash
python examples/composite_utility_demo.py
```

## Configuration

The module uses configuration from:
- `config/preferences.yaml` - User preferences and loyalty settings
- `config/merchant_penalties.yaml` - Merchant penalty configurations

## Examples

### Scenario 1: Travel Purchase

**Context**: Airline ticket purchase (MCC 4511), GOLD loyalty tier
**Expected Result**: Chase Sapphire Preferred (2x travel bonus)

### Scenario 2: Grocery Purchase

**Context**: Grocery store purchase (MCC 5411), GOLD loyalty tier
**Expected Result**: American Express Gold (4x grocery bonus)

### Scenario 3: Gas Station

**Context**: Gas station (MCC 5541), debit preference, NONE loyalty tier
**Expected Result**: Chase Freedom Unlimited (no annual fee, debit-friendly)

### Scenario 4: Restaurant

**Context**: Restaurant (MCC 5812), GOLD loyalty tier
**Expected Result**: American Express Gold (4x restaurant bonus)

## Performance Considerations

- **Caching**: Consider caching utility calculations for repeated scenarios
- **Batch Processing**: Calculate utilities for multiple cards in parallel
- **Lazy Loading**: Load preference and penalty configurations on demand
- **Optimization**: Use approximate calculations for real-time recommendations

## Future Enhancements

- Machine learning-based utility optimization
- Dynamic utility adjustment based on transaction history
- Real-time preference learning
- Geographic utility variations
- Seasonal utility adjustments
- Integration with external card databases


