"""Unit tests for AltWallet scoring system."""

from decimal import Decimal

import pytest

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
from altwallet_agent.policy import (
    RISK_SCORE_CHARGEBACKS,
    RISK_SCORE_HIGH_TICKET,
    RISK_SCORE_LOCATION_MISMATCH,
    RISK_SCORE_VELOCITY_FLAG,
)

# Import the scoring functions
from altwallet_agent.scoring import (
    ScoreResult,
    calculate_final_score,
    calculate_loyalty_boost,
    calculate_risk_score,
    determine_routing_hint,
    is_high_ticket,
    is_high_velocity,
    is_location_mismatch,
    score_transaction,
)


class TestScoringFunctions:
    """Test cases for scoring functions."""

    def test_calculate_risk_score_no_risk(self):
        """Test risk score calculation with no risk factors."""
        # Create a low-risk context
        context = self._create_test_context(
            cart_total=Decimal("50.00"),
            velocity_24h=5,
            chargebacks_12m=0,
            device_location={"city": "New York", "country": "US"},
            geo_location={"city": "New York", "country": "US"},
        )

        risk_score, signals = calculate_risk_score(context)

        assert risk_score == 0
        assert signals["location_mismatch"] is False
        assert signals["velocity_flag"] is False
        assert signals["chargebacks_present"] is False
        assert signals["high_ticket"] is False
        assert len(signals["risk_factors"]) == 0

    def test_calculate_risk_score_location_mismatch(self):
        """Test risk score with location mismatch."""
        context = self._create_test_context(
            device_location={"city": "New York", "country": "US"},
            geo_location={"city": "Los Angeles", "country": "US"},
        )

        risk_score, signals = calculate_risk_score(context)

        assert risk_score == RISK_SCORE_LOCATION_MISMATCH
        assert signals["location_mismatch"] is True
        assert "location_mismatch" in signals["risk_factors"]

    def test_calculate_risk_score_high_velocity(self):
        """Test risk score with high velocity."""
        context = self._create_test_context(velocity_24h=15)

        risk_score, signals = calculate_risk_score(context)

        assert risk_score == RISK_SCORE_VELOCITY_FLAG
        assert signals["velocity_flag"] is True
        assert "high_velocity_24h" in signals["risk_factors"]

    def test_calculate_risk_score_chargebacks(self):
        """Test risk score with chargebacks."""
        context = self._create_test_context(chargebacks_12m=2)

        risk_score, signals = calculate_risk_score(context)

        assert risk_score == RISK_SCORE_CHARGEBACKS
        assert signals["chargebacks_present"] is True
        assert "chargebacks_12m" in signals["risk_factors"]

    def test_calculate_risk_score_high_ticket(self):
        """Test risk score with high ticket amount."""
        context = self._create_test_context(cart_total=Decimal("600.00"))

        risk_score, signals = calculate_risk_score(context)

        assert risk_score == RISK_SCORE_HIGH_TICKET
        assert signals["high_ticket"] is True
        assert "high_ticket_amount" in signals["risk_factors"]

    def test_calculate_risk_score_multiple_factors(self):
        """Test risk score with multiple risk factors."""
        context = self._create_test_context(
            cart_total=Decimal("600.00"),
            velocity_24h=15,
            chargebacks_12m=1,
            device_location={"city": "New York", "country": "US"},
            geo_location={"city": "Los Angeles", "country": "US"},
        )

        risk_score, signals = calculate_risk_score(context)

        expected_risk = (
            RISK_SCORE_LOCATION_MISMATCH
            + RISK_SCORE_VELOCITY_FLAG
            + RISK_SCORE_CHARGEBACKS
            + RISK_SCORE_HIGH_TICKET
        )
        assert risk_score == expected_risk
        assert len(signals["risk_factors"]) == 4

    def test_calculate_loyalty_boost(self):
        """Test loyalty boost calculation for all tiers."""
        assert calculate_loyalty_boost(LoyaltyTier.NONE) == 0
        assert calculate_loyalty_boost(LoyaltyTier.SILVER) == 5
        assert calculate_loyalty_boost(LoyaltyTier.GOLD) == 10
        assert calculate_loyalty_boost(LoyaltyTier.PLATINUM) == 15

    def test_calculate_final_score(self):
        """Test final score calculation with various inputs."""
        # No risk, no loyalty boost
        assert calculate_final_score(0, 0) == 100

        # No risk, platinum loyalty
        assert calculate_final_score(0, 15) == 115

        # High risk, no loyalty boost
        assert calculate_final_score(50, 0) == 50

        # Very high risk (should clamp to 0)
        assert calculate_final_score(150, 0) == 0

        # High risk with loyalty boost
        assert calculate_final_score(30, 10) == 80

        # Maximum score with high loyalty
        assert calculate_final_score(0, 25) == 120  # Clamped to max

    def test_determine_routing_hint_merchant_preference(self):
        """Test routing hint with merchant network preferences."""
        context = self._create_test_context(merchant_network_preferences=["visa", "mc"])

        routing_hint = determine_routing_hint(context)
        assert routing_hint == "prefer_visa"

    def test_determine_routing_hint_mcc_based(self):
        """Test routing hint based on MCC."""
        context = self._create_test_context(merchant_mcc="5411")  # Grocery stores

        routing_hint = determine_routing_hint(context)
        assert routing_hint == "prefer_mc"

    def test_determine_routing_hint_default(self):
        """Test routing hint defaults to 'any'."""
        context = self._create_test_context(merchant_mcc="9999")  # Unknown MCC

        routing_hint = determine_routing_hint(context)
        assert routing_hint == "any"

    def test_score_transaction_complete(self):
        """Test complete scoring workflow."""
        context = self._create_test_context(
            cart_total=Decimal("600.00"),
            velocity_24h=15,
            chargebacks_12m=1,
            loyalty_tier=LoyaltyTier.GOLD,
            merchant_mcc="5411",
        )

        result = score_transaction(context)

        assert isinstance(result, ScoreResult)
        assert result.risk_score == (
            RISK_SCORE_HIGH_TICKET + RISK_SCORE_VELOCITY_FLAG + RISK_SCORE_CHARGEBACKS
        )
        assert result.loyalty_boost == 10
        assert result.routing_hint == "prefer_mc"
        assert "cart_total" in result.signals
        assert "customer_velocity_24h" in result.signals
        assert "loyalty_tier" in result.signals

    def test_pure_functions(self):
        """Test pure utility functions."""
        # Test location mismatch
        assert (
            is_location_mismatch(
                {"city": "NYC", "country": "US"}, {"city": "LA", "country": "US"}
            )
            is True
        )

        assert (
            is_location_mismatch(
                {"city": "NYC", "country": "US"}, {"city": "NYC", "country": "US"}
            )
            is False
        )

        # Test high velocity
        assert is_high_velocity(15) is True
        assert is_high_velocity(5) is False

        # Test high ticket
        assert is_high_ticket(Decimal("600.00")) is True
        assert is_high_ticket(Decimal("400.00")) is False

    def _create_test_context(
        self,
        cart_total: Decimal = Decimal("100.00"),
        velocity_24h: int = 5,
        chargebacks_12m: int = 0,
        loyalty_tier: LoyaltyTier = LoyaltyTier.NONE,
        device_location: dict = None,
        geo_location: dict = None,
        merchant_mcc: str = None,
        merchant_network_preferences: list = None,
    ) -> Context:
        """Helper method to create test contexts."""
        if device_location is None:
            device_location = {"city": "New York", "country": "US"}
        if geo_location is None:
            geo_location = {"city": "New York", "country": "US"}
        if merchant_network_preferences is None:
            merchant_network_preferences = []

        # Create cart with single item
        cart_item = CartItem(
            item="Test Item", unit_price=cart_total, qty=1, mcc=merchant_mcc
        )
        cart = Cart(items=[cart_item], currency="USD")

        # Create merchant
        merchant = Merchant(
            name="Test Merchant",
            mcc=merchant_mcc,
            network_preferences=merchant_network_preferences,
            location=geo_location,
        )

        # Create customer
        customer = Customer(
            id="test_customer",
            loyalty_tier=loyalty_tier,
            historical_velocity_24h=velocity_24h,
            chargebacks_12m=chargebacks_12m,
        )

        # Create device
        device = Device(
            ip="192.168.1.1", device_id="test_device", location=device_location
        )

        # Create geo
        geo = Geo(city=geo_location["city"], country=geo_location["country"])

        return Context(
            cart=cart, merchant=merchant, customer=customer, device=device, geo=geo
        )


class TestScoreResult:
    """Test cases for ScoreResult model."""

    def test_score_result_creation(self):
        """Test ScoreResult creation and validation."""
        result = ScoreResult.create(
            risk_score=30,
            loyalty_boost=10,
            final_score=80,
            routing_hint="prefer_visa",
            signals={"test": "value"},
        )

        assert result.risk_score == 30
        assert result.loyalty_boost == 10
        assert result.final_score == 80
        assert result.routing_hint == "prefer_visa"
        assert result.signals["test"] == "value"

    def test_score_result_bounds(self):
        """Test that scores are properly bounded."""
        # Test minimum bounds
        result = ScoreResult.create(
            risk_score=0, loyalty_boost=0, final_score=0, routing_hint="any", signals={}
        )
        assert result.final_score >= 0

        # Test maximum bounds
        result = ScoreResult.create(
            risk_score=0,
            loyalty_boost=0,
            final_score=120,
            routing_hint="any",
            signals={},
        )
        assert result.final_score <= 120


if __name__ == "__main__":
    pytest.main([__file__])
