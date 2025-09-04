#!/usr/bin/env python3
"""Demo script for Merchant Penalty Module.

This script demonstrates how the merchant penalty module calculates
penalties based on merchant preferences, network requirements, and MCC categories.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from decimal import Decimal

from altwallet_agent.merchant_penalty import MerchantPenalty
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


def create_sample_context(
    merchant_name: str = "Amazon.com",
    mcc: str = "5999",
    network_preferences: list = None,
) -> Context:
    """Create a sample context for testing."""
    if network_preferences is None:
        network_preferences = ["visa", "mastercard"]

    return Context(
        customer=Customer(
            id="customer_123",
            loyalty_tier=LoyaltyTier.GOLD,
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


def demo_exact_merchant_matches():
    """Demonstrate exact merchant name matching."""
    print("=== Exact Merchant Match Demo ===")

    penalty = MerchantPenalty()

    # Test exact matches for different merchants
    merchants_to_test = [
        ("amazon.com", "5999", "Online Retail"),
        ("walmart.com", "5311", "Department Store"),
        ("costco.com", "5411", "Warehouse Club"),
        ("delta.com", "4511", "Airline"),
        ("united.com", "4511", "Airline"),
    ]

    for merchant_name, mcc, category in merchants_to_test:
        context = create_sample_context(merchant_name, mcc)
        penalty_value = penalty.merchant_penalty(context)
        print(f"{merchant_name} ({category}): {penalty_value:.3f}")


def demo_fuzzy_merchant_matches():
    """Demonstrate fuzzy merchant name matching."""
    print("\n=== Fuzzy Merchant Match Demo ===")

    penalty = MerchantPenalty()

    # Test fuzzy matches
    fuzzy_tests = [
        ("amazon", "5999", "Should match amazon.com"),
        ("amzn", "5999", "Should match amazon.com"),
        ("walmart", "5311", "Should match walmart.com"),
        ("costco", "5411", "Should match costco.com"),
        ("delta-air", "4511", "Should match delta.com"),
    ]

    for merchant_name, mcc, description in fuzzy_tests:
        context = create_sample_context(merchant_name, mcc)
        penalty_value = penalty.merchant_penalty(context)
        print(f"{merchant_name} -> {description}: {penalty_value:.3f}")


def demo_mcc_family_fallback():
    """Demonstrate MCC family fallback when no exact merchant match."""
    print("\n=== MCC Family Fallback Demo ===")

    penalty = MerchantPenalty()

    # Test unknown merchants with known MCCs
    mcc_tests = [
        ("unknown_airline", "4511", "Airlines MCC"),
        ("unknown_grocery", "5411", "Grocery Stores MCC"),
        ("unknown_gas", "5541", "Gas Stations MCC"),
        ("unknown_restaurant", "5812", "Restaurants MCC"),
        ("unknown_online", "5999", "Online Retail MCC"),
    ]

    for merchant_name, mcc, description in mcc_tests:
        context = create_sample_context(merchant_name, mcc)
        penalty_value = penalty.merchant_penalty(context)
        print(f"{merchant_name} ({description}): {penalty_value:.3f}")


def demo_network_preferences():
    """Demonstrate network preference penalties."""
    print("\n=== Network Preference Demo ===")

    penalty = MerchantPenalty()

    # Test different network preferences
    network_tests = [
        (["debit"], "Debit preference"),
        (["visa"], "Visa preference"),
        (["mastercard"], "Mastercard preference"),
        (["amex"], "American Express preference"),
        (["discover"], "Discover preference"),
        (["no_amex"], "No American Express"),
        (["no_visa"], "No Visa"),
        (["no_mastercard"], "No Mastercard"),
        ([], "No preferences"),
    ]

    for network_prefs, description in network_tests:
        context = create_sample_context("test_merchant", "5411", network_prefs)
        penalty_value = penalty.merchant_penalty(context)
        print(f"{description}: {penalty_value:.3f}")


def demo_no_data_fallback():
    """Demonstrate fallback to base penalty when no data is available."""
    print("\n=== No Data Fallback Demo ===")

    penalty = MerchantPenalty()

    # Test completely unknown merchant and MCC
    context = create_sample_context("completely_unknown_merchant", "9999", [])
    penalty_value = penalty.merchant_penalty(context)
    print(f"Unknown merchant + unknown MCC: {penalty_value:.3f}")

    # Test with no network preferences
    context = create_sample_context("test_merchant", "9999", [])
    penalty_value = penalty.merchant_penalty(context)
    print(f"No network preferences: {penalty_value:.3f}")


def demo_merchant_name_normalization():
    """Demonstrate merchant name normalization."""
    print("\n=== Merchant Name Normalization Demo ===")

    penalty = MerchantPenalty()

    # Test various merchant name formats
    name_tests = [
        ("Amazon.com", "Standard format"),
        ("AMAZON.COM", "Uppercase"),
        ("amazon.com", "Lowercase"),
        ("Amazon-Store", "With hyphen"),
        ("Amazon Store", "With space"),
        ("Amazon.com.", "With trailing dot"),
    ]

    for merchant_name, description in name_tests:
        normalized = penalty._normalize_merchant_name(merchant_name)
        print(f"{merchant_name} -> {normalized} ({description})")


def demo_penalty_bounds():
    """Demonstrate that penalties are properly bounded."""
    print("\n=== Penalty Bounds Demo ===")

    penalty = MerchantPenalty()

    # Test extreme cases
    extreme_tests = [
        ("amazon.com", "5999", ["no_visa", "no_mastercard"], "Extreme preferences"),
        ("costco.com", "5411", ["debit"], "High penalty merchant + debit"),
        ("unknown_merchant", "9999", [], "Unknown everything"),
    ]

    for merchant_name, mcc, network_prefs, description in extreme_tests:
        context = create_sample_context(merchant_name, mcc, network_prefs)
        penalty_value = penalty.merchant_penalty(context)
        print(f"{description}: {penalty_value:.3f}")


def main():
    """Run all merchant penalty demos."""
    print("Merchant Penalty Module Demo")
    print("=" * 50)

    try:
        demo_exact_merchant_matches()
        demo_fuzzy_merchant_matches()
        demo_mcc_family_fallback()
        demo_network_preferences()
        demo_no_data_fallback()
        demo_merchant_name_normalization()
        demo_penalty_bounds()

        print("\n" + "=" * 50)
        print("Demo completed successfully!")

    except Exception as e:
        print(f"Error during demo: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
