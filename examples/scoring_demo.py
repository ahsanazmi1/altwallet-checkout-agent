#!/usr/bin/env python3
"""Demonstration of AltWallet Deterministic Scoring v1."""

import os
import sys
from decimal import Decimal

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

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
from altwallet_agent.scoring import score_transaction


def create_sample_context(
    cart_total: Decimal,
    velocity_24h: int,
    chargebacks_12m: int,
    loyalty_tier: LoyaltyTier,
    device_location: dict,
    geo_location: dict,
    merchant_mcc: str = None,
    merchant_name: str = "Sample Merchant",
) -> Context:
    """Create a sample context for demonstration."""

    # Create cart
    cart_item = CartItem(
        item="Sample Product", unit_price=cart_total, qty=1, mcc=merchant_mcc
    )
    cart = Cart(items=[cart_item], currency="USD")

    # Create merchant
    merchant = Merchant(
        name=merchant_name,
        mcc=merchant_mcc,
        network_preferences=[],
        location=geo_location,
    )

    # Create customer
    customer = Customer(
        id="demo_customer_001",
        loyalty_tier=loyalty_tier,
        historical_velocity_24h=velocity_24h,
        chargebacks_12m=chargebacks_12m,
    )

    # Create device
    device = Device(
        ip="192.168.1.100", device_id="demo_device_001", location=device_location
    )

    # Create geo
    geo = Geo(city=geo_location["city"], country=geo_location["country"])

    return Context(
        cart=cart, merchant=merchant, customer=customer, device=device, geo=geo
    )


def print_scoring_result(context: Context, result):
    """Print a formatted scoring result."""
    print(f"\n{'='*60}")
    print("SCORING RESULT")
    print(f"{'='*60}")

    print(f"Merchant: {context.merchant.name}")
    print(f"Cart Total: ${context.cart.total}")
    print(f"Customer Tier: {context.customer.loyalty_tier.value}")
    print(f"Velocity (24h): {context.customer.historical_velocity_24h}")
    print(f"Chargebacks (12m): {context.customer.chargebacks_12m}")

    print(f"\nRisk Score: {result.risk_score}")
    print(f"Loyalty Boost: +{result.loyalty_boost}")
    print(f"Final Score: {result.final_score}")
    print(f"Routing Hint: {result.routing_hint}")

    print("\nRisk Factors:")
    for factor in result.signals.get("risk_factors", []):
        print(f"  - {factor}")

    print("\nSignals:")
    for key, value in result.signals.items():
        if key not in ["risk_factors"]:
            print(f"  {key}: {value}")


def main():
    """Run scoring demonstrations."""
    print("AltWallet Deterministic Scoring v1 Demo")
    print("=" * 60)

    # Example 1: Low-risk transaction
    print("\n1. LOW-RISK TRANSACTION")
    context1 = create_sample_context(
        cart_total=Decimal("50.00"),
        velocity_24h=3,
        chargebacks_12m=0,
        loyalty_tier=LoyaltyTier.SILVER,
        device_location={"city": "New York", "country": "US"},
        geo_location={"city": "New York", "country": "US"},
        merchant_mcc="5411",
        merchant_name="Local Grocery Store",
    )

    result1 = score_transaction(context1)
    print_scoring_result(context1, result1)

    # Example 2: High-risk transaction
    print("\n2. HIGH-RISK TRANSACTION")
    context2 = create_sample_context(
        cart_total=Decimal("800.00"),
        velocity_24h=15,
        chargebacks_12m=2,
        loyalty_tier=LoyaltyTier.NONE,
        device_location={"city": "New York", "country": "US"},
        geo_location={"city": "Los Angeles", "country": "US"},
        merchant_mcc="5541",
        merchant_name="Gas Station",
    )

    result2 = score_transaction(context2)
    print_scoring_result(context2, result2)

    # Example 3: Premium customer with some risk
    print("\n3. PREMIUM CUSTOMER WITH MODERATE RISK")
    context3 = create_sample_context(
        cart_total=Decimal("600.00"),
        velocity_24h=8,
        chargebacks_12m=0,
        loyalty_tier=LoyaltyTier.PLATINUM,
        device_location={"city": "San Francisco", "country": "US"},
        geo_location={"city": "San Francisco", "country": "US"},
        merchant_mcc="7011",
        merchant_name="Luxury Hotel",
    )

    result3 = score_transaction(context3)
    print_scoring_result(context3, result3)

    # Example 4: International transaction
    print("\n4. INTERNATIONAL TRANSACTION")
    context4 = create_sample_context(
        cart_total=Decimal("300.00"),
        velocity_24h=5,
        chargebacks_12m=0,
        loyalty_tier=LoyaltyTier.GOLD,
        device_location={"city": "London", "country": "UK"},
        geo_location={"city": "Paris", "country": "FR"},
        merchant_mcc="4722",
        merchant_name="Travel Agency",
    )

    result4 = score_transaction(context4)
    print_scoring_result(context4, result4)

    print(f"\n{'='*60}")
    print("DEMO COMPLETE")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
