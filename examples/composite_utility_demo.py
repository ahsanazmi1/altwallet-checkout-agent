#!/usr/bin/env python3
"""Demo script for Composite Utility Module.

This script demonstrates how the composite utility module calculates
utility scores and ranks cards based on different scenarios.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from decimal import Decimal

from altwallet_agent.composite_utility import CompositeUtility
from altwallet_agent.models import (
    Cart,
    CartItem,
    Context,
    Customer,
    Device,
    Geo,
    LoyaltyTier,
    Merchant,
)


def create_sample_cards():
    """Create sample cards for demonstration."""
    return [
        {
            "card_id": "chase_sapphire_preferred",
            "name": "Chase Sapphire Preferred",
            "cashback_rate": 0.02,
            "category_bonuses": {
                "4511": 2.0,  # Airlines
                "5812": 2.0,  # Restaurants
                "4722": 2.0,  # Travel agencies
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
        {
            "card_id": "chase_freedom_unlimited",
            "name": "Chase Freedom Unlimited",
            "cashback_rate": 0.015,
            "category_bonuses": {},
            "issuer": "chase",
            "annual_fee": 0,
            "rewards_type": "cashback",
        },
        {
            "card_id": "citi_double_cash",
            "name": "Citi Double Cash",
            "cashback_rate": 0.02,
            "category_bonuses": {},
            "issuer": "citi",
            "annual_fee": 0,
            "rewards_type": "cashback",
        },
    ]


def create_sample_context(
    loyalty_tier: LoyaltyTier = LoyaltyTier.GOLD,
    mcc: str = "5411",
    merchant_name: str = "Sample Store",
    network_preferences: list = None,
) -> Context:
    """Create a sample context for testing."""
    if network_preferences is None:
        network_preferences = ["visa", "mastercard"]

    return Context(
        customer=Customer(
            id="customer_123",
            loyalty_tier=loyalty_tier,
            historical_velocity_24h=2,
            chargebacks_12m=0,
        ),
        merchant=Merchant(
            name=merchant_name,
            mcc=mcc,
            network_preferences=network_preferences,
            location={"city": "New York", "country": "US"},
        ),
        cart=Cart(
            items=[
                CartItem(
                    item="Sample Item",
                    unit_price=Decimal("100.00"),
                    qty=1,
                    mcc=mcc,
                    merchant_category="Sample Category",
                )
            ],
            currency="USD",
        ),
        device=Device(
            ip="192.168.1.1",
            device_id="demo_device_123",
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


def demo_basic_utility_calculation():
    """Demonstrate basic utility calculation."""
    print("=== Basic Utility Calculation Demo ===")

    utility = CompositeUtility()
    cards = create_sample_cards()
    context = create_sample_context()

    print(f"Calculating utility for {len(cards)} cards...")

    for card in cards:
        result = utility.calculate_card_utility(card, context)
        print(f"\n{card['name']}:")
        print(f"  Utility Score: {result['utility_score']:.4f}")
        print(f"  P(Approval): {result['components']['p_approval']:.3f}")
        print(f"  Expected Rewards: {result['components']['expected_rewards']:.3f}")
        print(f"  Preference Weight: {result['components']['preference_weight']:.3f}")
        print(f"  Merchant Penalty: {result['components']['merchant_penalty']:.3f}")


def demo_travel_vs_grocery_rank_shifts():
    """Demonstrate rank shifts between travel and grocery scenarios."""
    print("\n=== Travel vs Grocery Rank Shifts Demo ===")

    utility = CompositeUtility()
    cards = create_sample_cards()

    # Travel scenario (airlines)
    travel_context = create_sample_context(mcc="4511", merchant_name="Delta Airlines")

    # Grocery scenario
    grocery_context = create_sample_context(mcc="5411", merchant_name="Whole Foods")

    print("Travel Scenario (Airlines - MCC 4511):")
    travel_ranked = utility.rank_cards_by_utility(cards, travel_context)
    for i, card in enumerate(travel_ranked[:3]):  # Top 3
        print(f"  {i+1}. {card['card_name']}: {card['utility_score']:.4f}")

    print("\nGrocery Scenario (Grocery Stores - MCC 5411):")
    grocery_ranked = utility.rank_cards_by_utility(cards, grocery_context)
    for i, card in enumerate(grocery_ranked[:3]):  # Top 3
        print(f"  {i+1}. {card['card_name']}: {card['utility_score']:.4f}")

    # Show rank changes
    print("\nRank Changes:")
    travel_top = travel_ranked[0]["card_name"]
    grocery_top = grocery_ranked[0]["card_name"]
    print(f"  Travel top: {travel_top}")
    print(f"  Grocery top: {grocery_top}")
    if travel_top != grocery_top:
        print(f"  ✓ Rank shift detected: {travel_top} vs {grocery_top}")


def demo_loyalty_tier_rank_shifts():
    """Demonstrate rank shifts between different loyalty tiers."""
    print("\n=== Loyalty Tier Rank Shifts Demo ===")

    utility = CompositeUtility()
    cards = create_sample_cards()

    # GOLD loyalty tier
    gold_context = create_sample_context(loyalty_tier=LoyaltyTier.GOLD)

    # NONE loyalty tier
    none_context = create_sample_context(loyalty_tier=LoyaltyTier.NONE)

    print("GOLD Loyalty Tier:")
    gold_ranked = utility.rank_cards_by_utility(cards, gold_context)
    for i, card in enumerate(gold_ranked[:3]):  # Top 3
        print(f"  {i+1}. {card['card_name']}: {card['utility_score']:.4f}")

    print("\nNONE Loyalty Tier:")
    none_ranked = utility.rank_cards_by_utility(cards, none_context)
    for i, card in enumerate(none_ranked[:3]):  # Top 3
        print(f"  {i+1}. {card['card_name']}: {card['utility_score']:.4f}")

    # Show rank changes
    print("\nRank Changes:")
    gold_top = gold_ranked[0]["card_name"]
    none_top = none_ranked[0]["card_name"]
    print(f"  GOLD top: {gold_top}")
    print(f"  NONE top: {none_top}")
    if gold_top != none_top:
        print(f"  ✓ Rank shift detected: {gold_top} vs {none_top}")


def demo_merchant_debit_preference_rank_shifts():
    """Demonstrate rank shifts when merchant prefers debit."""
    print("\n=== Merchant Debit Preference Rank Shifts Demo ===")

    utility = CompositeUtility()
    cards = create_sample_cards()

    # Debit preference scenario
    debit_context = create_sample_context(
        network_preferences=["debit"], merchant_name="Gas Station"
    )

    # No preference scenario
    no_pref_context = create_sample_context(
        network_preferences=[], merchant_name="Online Store"
    )

    print("Debit Preference Scenario:")
    debit_ranked = utility.rank_cards_by_utility(cards, debit_context)
    for i, card in enumerate(debit_ranked[:3]):  # Top 3
        print(f"  {i+1}. {card['card_name']}: {card['utility_score']:.4f}")

    print("\nNo Preference Scenario:")
    no_pref_ranked = utility.rank_cards_by_utility(cards, no_pref_context)
    for i, card in enumerate(no_pref_ranked[:3]):  # Top 3
        print(f"  {i+1}. {card['card_name']}: {card['utility_score']:.4f}")

    # Show rank changes
    print("\nRank Changes:")
    debit_top = debit_ranked[0]["card_name"]
    no_pref_top = no_pref_ranked[0]["card_name"]
    print(f"  Debit preference top: {debit_top}")
    print(f"  No preference top: {no_pref_top}")
    if debit_top != no_pref_top:
        print(f"  ✓ Rank shift detected: {debit_top} vs {no_pref_top}")


def demo_utility_analysis():
    """Demonstrate utility component analysis."""
    print("\n=== Utility Component Analysis Demo ===")

    utility = CompositeUtility()
    cards = create_sample_cards()
    context = create_sample_context()

    analysis = utility.analyze_utility_components(cards, context)

    print(f"Total cards analyzed: {analysis['total_cards']}")
    print(f"Top card: {analysis['top_card']}")
    print(f"Top utility score: {analysis['top_utility']:.4f}")

    print("\nUtility Score Range:")
    print(f"  Min: {analysis['utility_range']['min']:.4f}")
    print(f"  Max: {analysis['utility_range']['max']:.4f}")
    print(f"  Avg: {analysis['utility_range']['avg']:.4f}")

    print("\nComponent Ranges:")
    for component, ranges in analysis["component_ranges"].items():
        print(f"  {component}: {ranges['min']:.3f} - {ranges['max']:.3f}")


def demo_composite_utility_formula():
    """Demonstrate the composite utility formula."""
    print("\n=== Composite Utility Formula Demo ===")

    utility = CompositeUtility()
    cards = create_sample_cards()
    context = create_sample_context()

    # Calculate utility for the first card
    card = cards[0]  # Chase Sapphire Preferred
    result = utility.calculate_card_utility(card, context)

    print(f"Card: {card['name']}")
    print(
        "Formula: utility = p_approval × expected_rewards × preference_weight × merchant_penalty"
    )
    print()

    p_approval = result["components"]["p_approval"]
    expected_rewards = result["components"]["expected_rewards"]
    preference_weight = result["components"]["preference_weight"]
    merchant_penalty = result["components"]["merchant_penalty"]
    final_utility = result["utility_score"]

    print("Components:")
    print(f"  p_approval = {p_approval:.3f}")
    print(f"  expected_rewards = {expected_rewards:.3f}")
    print(f"  preference_weight = {preference_weight:.3f}")
    print(f"  merchant_penalty = {merchant_penalty:.3f}")
    print()
    print("Calculation:")
    print(
        f"  utility = {p_approval:.3f} × {expected_rewards:.3f} × {preference_weight:.3f} × {merchant_penalty:.3f}"
    )
    print(f"  utility = {final_utility:.4f}")


def main():
    """Run all composite utility demos."""
    print("Composite Utility Module Demo")
    print("=" * 50)

    try:
        demo_basic_utility_calculation()
        demo_travel_vs_grocery_rank_shifts()
        demo_loyalty_tier_rank_shifts()
        demo_merchant_debit_preference_rank_shifts()
        demo_utility_analysis()
        demo_composite_utility_formula()

        print("\n" + "=" * 50)
        print("Demo completed successfully!")
        print("\nKey Insights:")
        print(
            "- Utility combines approval probability, rewards, preferences, and penalties"
        )
        print(
            "- Rank shifts occur based on MCC categories, loyalty tiers, and merchant preferences"
        )
        print(
            "- The formula ensures optimal card selection for each transaction context"
        )

    except Exception as e:
        print(f"Error during demo: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
