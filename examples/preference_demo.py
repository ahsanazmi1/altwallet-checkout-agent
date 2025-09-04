#!/usr/bin/env python3
"""Demo script for Preference & Loyalty Weighting Module.

This script demonstrates how the preference weighting module calculates
multiplicative weights for card recommendations based on user preferences,
loyalty tiers, category boosts, and issuer promotions.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from altwallet_agent.preference_weighting import PreferenceWeighting
from altwallet_agent.models import (
    Context,
    Customer,
    Merchant,
    Cart,
    CartItem,
    LoyaltyTier,
    Device,
    Geo,
)
from decimal import Decimal


def create_sample_context(
    loyalty_tier: LoyaltyTier = LoyaltyTier.NONE,
    mcc: str = "5411",
    merchant_name: str = "Sample Store",
) -> Context:
    """Create a sample context for testing."""
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
            network_preferences=["visa", "mastercard"],
            location={"city": "New York", "country": "US"},
        ),
        cart=Cart(
            items=[
                CartItem(
                    item="Sample Item",
                    unit_price=Decimal("50.00"),
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


def create_sample_cards() -> list[dict]:
    """Create sample card data for testing."""
    return [
        {
            "id": "chase_sapphire_preferred",
            "name": "Chase Sapphire Preferred",
            "issuer": "Chase",
            "annual_fee": 95,
            "base_rewards_rate": 0.02,
            "rewards_type": "points",
            "signup_bonus_points": 60000,
            "category_bonuses": {
                "travel": 0.025,
                "dining": 0.025,
                "online_grocery": 0.025,
            },
            "travel_benefits": ["Trip cancellation insurance"],
            "foreign_transaction_fee": 0.0,
        },
        {
            "id": "amex_gold",
            "name": "American Express Gold",
            "issuer": "American Express",
            "annual_fee": 250,
            "base_rewards_rate": 0.01,
            "rewards_type": "points",
            "signup_bonus_points": 60000,
            "category_bonuses": {
                "dining": 0.04,
                "grocery_stores": 0.04,
                "airfare": 0.03,
            },
            "travel_benefits": ["Flight credit", "Hotel credit"],
            "foreign_transaction_fee": 0.0275,
        },
        {
            "id": "citi_double_cash",
            "name": "Citi Double Cash",
            "issuer": "Citi",
            "annual_fee": 0,
            "base_rewards_rate": 0.02,
            "rewards_type": "cashback",
            "signup_bonus_points": 0,
            "category_bonuses": {},
            "travel_benefits": [],
            "foreign_transaction_fee": 0.03,
        },
        {
            "id": "capital_one_venture",
            "name": "Capital One Venture",
            "issuer": "Capital One",
            "annual_fee": 95,
            "base_rewards_rate": 0.02,
            "rewards_type": "points",
            "signup_bonus_points": 75000,
            "category_bonuses": {},
            "travel_benefits": ["Travel credit"],
            "foreign_transaction_fee": 0.0,
        },
    ]


def demo_loyalty_tier_weights():
    """Demonstrate how loyalty tiers affect card weights."""
    print("=== Loyalty Tier Weight Demo ===")

    weighting = PreferenceWeighting()
    cards = create_sample_cards()

    # Test different loyalty tiers
    loyalty_tiers = [
        LoyaltyTier.NONE,
        LoyaltyTier.SILVER,
        LoyaltyTier.GOLD,
        LoyaltyTier.PLATINUM,
        LoyaltyTier.DIAMOND,
    ]

    for tier in loyalty_tiers:
        print(f"\nLoyalty Tier: {tier.value}")
        context = create_sample_context(loyalty_tier=tier)

        for card in cards:
            weight = weighting.preference_weight(card, context)
            print(f"  {card['name']}: {weight:.3f}")


def demo_category_boosts():
    """Demonstrate how merchant categories affect card weights."""
    print("\n=== Category Boost Demo ===")

    weighting = PreferenceWeighting()
    cards = create_sample_cards()

    # Test different merchant categories
    categories = [
        ("5411", "Grocery Store"),
        ("5812", "Restaurant"),
        ("4511", "Airline"),
        ("5541", "Gas Station"),
        ("5311", "Department Store"),
    ]

    for mcc, category_name in categories:
        print(f"\nCategory: {category_name} (MCC: {mcc})")
        context = create_sample_context(mcc=mcc, merchant_name=category_name)

        for card in cards:
            weight = weighting.preference_weight(card, context)
            print(f"  {card['name']}: {weight:.3f}")


def demo_user_preferences():
    """Demonstrate how user preferences affect card weights."""
    print("\n=== User Preference Demo ===")

    # Create weighting with custom config
    weighting = PreferenceWeighting()
    cards = create_sample_cards()
    context = create_sample_context()

    print("\nCashback vs Points Preference:")
    print("  Cashback preference (0.8):")
    weighting.config["user_preferences"]["cashback_vs_points_weight"] = 0.8
    for card in cards:
        weight = weighting.preference_weight(card, context)
        print(f"    {card['name']}: {weight:.3f}")

    print("\n  Points preference (0.2):")
    weighting.config["user_preferences"]["cashback_vs_points_weight"] = 0.2
    for card in cards:
        weight = weighting.preference_weight(card, context)
        print(f"    {card['name']}: {weight:.3f}")

    print("\nAnnual Fee Tolerance:")
    print("  Fee-averse (0.1):")
    weighting.config["user_preferences"]["annual_fee_tolerance"] = 0.1
    for card in cards:
        weight = weighting.preference_weight(card, context)
        print(f"    {card['name']}: {weight:.3f}")

    print("\n  Fee-agnostic (0.9):")
    weighting.config["user_preferences"]["annual_fee_tolerance"] = 0.9
    for card in cards:
        weight = weighting.preference_weight(card, context)
        print(f"    {card['name']}: {weight:.3f}")


def demo_issuer_affinity():
    """Demonstrate how issuer affinity affects card weights."""
    print("\n=== Issuer Affinity Demo ===")

    weighting = PreferenceWeighting()
    cards = create_sample_cards()
    context = create_sample_context()

    print("\nChase Affinity (0.2):")
    weighting.config["user_preferences"]["issuer_affinity"]["chase"] = 0.2
    for card in cards:
        weight = weighting.preference_weight(card, context)
        print(f"  {card['name']}: {weight:.3f}")

    print("\nAmerican Express Affinity (0.2):")
    weighting.config["user_preferences"]["issuer_affinity"]["chase"] = 0.0
    weighting.config["user_preferences"]["issuer_affinity"]["american_express"] = 0.2
    for card in cards:
        weight = weighting.preference_weight(card, context)
        print(f"  {card['name']}: {weight:.3f}")


def main():
    """Run all preference weighting demos."""
    print("Preference & Loyalty Weighting Module Demo")
    print("=" * 50)

    try:
        demo_loyalty_tier_weights()
        demo_category_boosts()
        demo_user_preferences()
        demo_issuer_affinity()

        print("\n" + "=" * 50)
        print("Demo completed successfully!")

    except Exception as e:
        print(f"Error during demo: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
