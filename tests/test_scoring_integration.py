"""Integration test for AltWallet scoring system."""

import sys
import os
from decimal import Decimal

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_scoring_integration():
    """Test that the scoring system works end-to-end."""

    # Import the scoring components
    from altwallet_agent.scoring import score_transaction, ScoreResult
    from altwallet_agent.models import (
        Context,
        Cart,
        CartItem,
        Merchant,
        Customer,
        Device,
        Geo,
        LoyaltyTier,
    )
    from altwallet_agent.policy import LOYALTY_BOOST_VALUES

    # Create a test context
    cart_item = CartItem(
        item="Test Product", unit_price=Decimal("100.00"), qty=1, mcc="5411"
    )
    cart = Cart(items=[cart_item], currency="USD")

    merchant = Merchant(
        name="Test Merchant",
        mcc="5411",
        network_preferences=[],
        location={"city": "New York", "country": "US"},
    )

    customer = Customer(
        id="test_customer",
        loyalty_tier=LoyaltyTier.GOLD,
        historical_velocity_24h=5,
        chargebacks_12m=0,
    )

    device = Device(
        ip="192.168.1.1",
        device_id="test_device",
        location={"city": "New York", "country": "US"},
    )

    geo = Geo(city="New York", country="US")

    context = Context(
        cart=cart, merchant=merchant, customer=customer, device=device, geo=geo
    )

    # Score the transaction
    result = score_transaction(context)

    # Verify the result
    assert isinstance(result, ScoreResult)
    assert result.risk_score == 0  # No risk factors
    assert result.loyalty_boost == LOYALTY_BOOST_VALUES["GOLD"]
    assert result.final_score == 100 + LOYALTY_BOOST_VALUES["GOLD"]
    assert result.routing_hint == "prefer_mc"  # MCC 5411 maps to MC
    assert "cart_total" in result.signals
    assert "customer_velocity_24h" in result.signals
    assert "loyalty_tier" in result.signals

    print("✅ Integration test passed!")
    print(f"Risk Score: {result.risk_score}")
    print(f"Loyalty Boost: {result.loyalty_boost}")
    print(f"Final Score: {result.final_score}")
    print(f"Routing Hint: {result.routing_hint}")


def test_high_risk_scenario():
    """Test a high-risk transaction scenario."""

    from altwallet_agent.scoring import score_transaction
    from altwallet_agent.models import (
        Context,
        Cart,
        CartItem,
        Merchant,
        Customer,
        Device,
        Geo,
        LoyaltyTier,
    )
    from altwallet_agent.policy import (
        RISK_SCORE_LOCATION_MISMATCH,
        RISK_SCORE_VELOCITY_FLAG,
        RISK_SCORE_CHARGEBACKS,
        RISK_SCORE_HIGH_TICKET,
    )

    # Create high-risk context
    cart_item = CartItem(
        item="Expensive Item", unit_price=Decimal("600.00"), qty=1, mcc="5732"
    )
    cart = Cart(items=[cart_item], currency="USD")

    merchant = Merchant(
        name="Electronics Store",
        mcc="5732",
        network_preferences=[],
        location={"city": "Los Angeles", "country": "US"},
    )

    customer = Customer(
        id="risky_customer",
        loyalty_tier=LoyaltyTier.NONE,
        historical_velocity_24h=15,
        chargebacks_12m=2,
    )

    device = Device(
        ip="192.168.1.1",
        device_id="test_device",
        location={"city": "New York", "country": "US"},
    )

    geo = Geo(city="Los Angeles", country="US")

    context = Context(
        cart=cart, merchant=merchant, customer=customer, device=device, geo=geo
    )

    # Score the transaction
    result = score_transaction(context)

    # Calculate expected risk score
    expected_risk = (
        RISK_SCORE_LOCATION_MISMATCH  # 30
        + RISK_SCORE_VELOCITY_FLAG  # 20
        + RISK_SCORE_CHARGEBACKS  # 25
        + RISK_SCORE_HIGH_TICKET  # 10
    )  # Total: 85

    assert result.risk_score == expected_risk
    assert result.loyalty_boost == 0
    assert result.final_score == max(0, 100 - expected_risk) + 0  # 15
    assert result.routing_hint == "prefer_mc"  # MCC 5732 maps to MC

    print("✅ High-risk scenario test passed!")
    print(f"Risk Score: {result.risk_score}")
    print(f"Final Score: {result.final_score}")
    print(f"Risk Factors: {result.signals['risk_factors']}")


if __name__ == "__main__":
    print("Running AltWallet Scoring Integration Tests")
    print("=" * 50)

    try:
        test_scoring_integration()
        test_high_risk_scenario()
        print("\n🎉 All integration tests passed!")
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        sys.exit(1)
