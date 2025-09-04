#!/usr/bin/env python3
"""Demo script for the AltWallet Checkout Agent Decisioning Module.

This script demonstrates how to use the decisioning module to make
transaction decisions and get standardized contracts with routing hints.
"""

import json
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import after path setup
from altwallet_agent.decisioning import DecisionEngine
from altwallet_agent.logger import configure_logging
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


def create_sample_context() -> Context:
    """Create a sample transaction context for demonstration."""

    # Create cart with items
    cart_items = [
        CartItem(
            item="Laptop",
            unit_price="1200.00",
            qty=1,
            mcc="5732",
            merchant_category="Electronics Store",
        ),
        CartItem(
            item="Mouse",
            unit_price="25.00",
            qty=1,
            mcc="5732",
            merchant_category="Electronics Store",
        ),
    ]

    cart = Cart(items=cart_items, currency="USD")

    # Create merchant
    merchant = Merchant(
        name="TechStore Online",
        mcc="5732",
        network_preferences=["visa", "mc"],
        location={"city": "San Francisco", "country": "USA"},
    )

    # Create customer
    customer = Customer(
        id="cust_12345",
        loyalty_tier=LoyaltyTier.GOLD,
        historical_velocity_24h=3,
        chargebacks_12m=0,
    )

    # Create device
    device = Device(
        ip="192.168.1.100",
        device_id="dev_67890",
        ip_distance_km=0.5,
        location={"city": "San Francisco", "country": "USA"},
    )

    # Create geo location
    geo = Geo(
        city="San Francisco", region="CA", country="USA", lat=37.7749, lon=-122.4194
    )

    return Context(
        cart=cart, merchant=merchant, customer=customer, device=device, geo=geo
    )


def create_risky_context() -> Context:
    """Create a risky transaction context for demonstration."""

    # Create cart with high-value items
    cart_items = [
        CartItem(
            item="Diamond Ring",
            unit_price="5000.00",
            qty=1,
            mcc="5944",
            merchant_category="Jewelry Store",
        )
    ]

    cart = Cart(items=cart_items, currency="USD")

    # Create merchant
    merchant = Merchant(
        name="Luxury Jewelers",
        mcc="5944",
        network_preferences=["visa"],
        location={"city": "New York", "country": "USA"},
    )

    # Create risky customer
    customer = Customer(
        id="cust_risky_001",
        loyalty_tier=LoyaltyTier.NONE,
        historical_velocity_24h=15,  # High velocity
        chargebacks_12m=2,  # Has chargebacks
    )

    # Create device with location mismatch
    device = Device(
        ip="203.0.113.1",
        device_id="dev_risky_001",
        ip_distance_km=5000.0,  # Large distance
        location={"city": "Los Angeles", "country": "USA"},  # Different city
    )

    # Create geo location
    geo = Geo(city="New York", region="NY", country="USA", lat=40.7128, lon=-74.0060)

    return Context(
        cart=cart, merchant=merchant, customer=customer, device=device, geo=geo
    )


def demonstrate_decisioning():
    """Demonstrate the decisioning module functionality."""

    print("🚀 AltWallet Checkout Agent - Decisioning Module Demo")
    print("=" * 60)

    # Create decision engine
    engine = DecisionEngine()

    # Test 1: Normal transaction
    print("\n📋 Test 1: Normal Transaction (Expected: APPROVE)")
    print("-" * 50)

    normal_context = create_sample_context()
    normal_decision = engine.make_decision(normal_context, "txn_normal_001")

    print(f"Decision: {normal_decision.decision.value}")
    print(f"Final Score: {normal_decision.score_result.final_score}")
    print(f"Confidence: {normal_decision.confidence:.2f}")
    print(f"Actions Applied: {len(normal_decision.actions)}")
    print(f"Reasons: {len(normal_decision.reasons)}")

    # Show routing hints
    print("\nRouting Hints:")
    print(f"  • Preferred Network: {normal_decision.routing_hint.preferred_network}")
    print(f"  • Preferred Acquirer: {normal_decision.routing_hint.preferred_acquirer}")
    print(
        f"  • Penalty/Incentive: {normal_decision.routing_hint.penalty_or_incentive.value}"
    )
    print(f"  • Approval Odds: {normal_decision.routing_hint.approval_odds:.3f}")
    print(
        f"  • Network Preferences: {normal_decision.routing_hint.network_preferences}"
    )
    print(f"  • MCC-based Hint: {normal_decision.routing_hint.mcc_based_hint}")
    print(f"  • Routing Confidence: {normal_decision.routing_hint.confidence:.2f}")

    # Show actions
    if normal_decision.actions:
        print("\nActions Applied:")
        for action in normal_decision.actions:
            print(f"  • {action.action_type.value}: {action.description}")

    # Test 2: Risky transaction
    print("\n📋 Test 2: Risky Transaction (Expected: REVIEW/DECLINE)")
    print("-" * 50)

    risky_context = create_risky_context()
    risky_decision = engine.make_decision(risky_context, "txn_risky_001")

    print(f"Decision: {risky_decision.decision.value}")
    print(f"Final Score: {risky_decision.score_result.final_score}")
    print(f"Confidence: {risky_decision.confidence:.2f}")
    print(f"Actions Applied: {len(risky_decision.actions)}")
    print(f"Reasons: {len(risky_decision.reasons)}")

    # Show routing hints
    print("\nRouting Hints:")
    print(f"  • Preferred Network: {risky_decision.routing_hint.preferred_network}")
    print(f"  • Preferred Acquirer: {risky_decision.routing_hint.preferred_acquirer}")
    print(
        f"  • Penalty/Incentive: {risky_decision.routing_hint.penalty_or_incentive.value}"
    )
    print(f"  • Approval Odds: {risky_decision.routing_hint.approval_odds:.3f}")
    print(f"  • Network Preferences: {risky_decision.routing_hint.network_preferences}")
    print(f"  • MCC-based Hint: {risky_decision.routing_hint.mcc_based_hint}")
    print(f"  • Routing Confidence: {risky_decision.routing_hint.confidence:.2f}")

    # Show actions
    if risky_decision.actions:
        print("\nActions Applied:")
        for action in risky_decision.actions:
            print(f"  • {action.action_type.value}: {action.description}")

    # Show reasons
    if risky_decision.reasons:
        print("\nDecision Reasons:")
        for reason in risky_decision.reasons:
            print(f"  • {reason.feature_name}: {reason.description}")

    # Test 3: JSON serialization
    print("\n📋 Test 3: JSON Serialization")
    print("-" * 50)

    # Convert to JSON
    normal_json = normal_decision.to_json()
    risky_json = risky_decision.to_json()

    print(f"Normal transaction JSON length: {len(normal_json)} characters")
    print(f"Risky transaction JSON length: {len(risky_json)} characters")

    # Test 4: Dictionary conversion
    print("\n📋 Test 4: Dictionary Conversion")
    print("-" * 50)

    normal_dict = normal_decision.to_dict()
    risky_dict = risky_decision.to_dict()

    print(f"Normal transaction dict keys: {list(normal_dict.keys())}")
    print(f"Risky transaction dict keys: {list(risky_dict.keys())}")

    # Test 5: Convenience function
    print("\n📋 Test 5: Convenience Function")
    print("-" * 50)

    from altwallet_agent.decisioning import make_transaction_decision

    quick_decision = make_transaction_decision(normal_context, "txn_quick_001")
    print(f"Quick decision result: {quick_decision.decision.value}")
    print(f"Using convenience function: {quick_decision.transaction_id}")

    print("\n✅ Decisioning module demo completed successfully!")

    return normal_decision, risky_decision


def main():
    """Main function to run the demo."""
    try:
        # Configure logging
        configure_logging()

        # Run the demo
        normal_decision, risky_decision = demonstrate_decisioning()

        # Save results to files for inspection
        with open("normal_decision.json", "w") as f:
            json.dump(normal_decision.to_dict(), f, indent=2, default=str)

        with open("risky_decision.json", "w") as f:
            json.dump(risky_decision.to_dict(), f, indent=2, default=str)

        print("\n💾 Decision results saved to:")
        print("  • normal_decision.json")
        print("  • risky_decision.json")

    except Exception as e:
        print(f"❌ Error running demo: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
