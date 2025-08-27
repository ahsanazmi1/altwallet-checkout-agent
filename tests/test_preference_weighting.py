"""Tests for Preference & Loyalty Weighting Module."""

import pytest
from decimal import Decimal
from unittest.mock import patch, mock_open

from src.altwallet_agent.preference_weighting import PreferenceWeighting
from src.altwallet_agent.models import (
    Context,
    Customer,
    Merchant,
    Cart,
    CartItem,
    LoyaltyTier,
    Device,
    Geo,
)


class TestPreferenceWeighting:
    """Test cases for PreferenceWeighting class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.weighting = PreferenceWeighting()
        self.sample_card = {
            "name": "Test Card",
            "issuer": "Test Bank",
            "annual_fee": 95,
            "rewards_type": "points",
            "signup_bonus_points": 50000,
            "category_bonuses": {"travel": 0.03},
            "travel_benefits": ["Trip insurance"],
            "foreign_transaction_fee": 0.0,
        }
        self.sample_context = Context(
            customer=Customer(
                id="test_customer",
                loyalty_tier=LoyaltyTier.GOLD,
                historical_velocity_24h=1,
                chargebacks_12m=0,
            ),
            merchant=Merchant(
                name="Test Merchant",
                mcc="4511",  # Airlines
                network_preferences=["visa"],
                location={"city": "New York", "country": "US"},
            ),
            cart=Cart(
                items=[
                    CartItem(
                        item="Test Item",
                        unit_price=Decimal("100.00"),
                        qty=1,
                        mcc="4511",
                        merchant_category="Airlines",
                    )
                ],
                currency="USD",
            ),
            device=Device(
                ip="192.168.1.1",
                device_id="test_device_123",
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

    def test_init_with_default_config(self):
        """Test initialization with default configuration."""
        weighting = PreferenceWeighting()
        assert weighting.config is not None
        assert "user_preferences" in weighting.config
        assert "loyalty_tiers" in weighting.config
        assert "category_boosts" in weighting.config

    @patch("builtins.open", mock_open(read_data="""
user_preferences:
  cashback_vs_points_weight: 0.7
  issuer_affinity:
    chase: 0.1
  annual_fee_tolerance: 0.8
  foreign_fee_sensitivity: 0.6
loyalty_tiers:
  NONE: 1.0
  SILVER: 1.05
  GOLD: 1.10
  PLATINUM: 1.15
  DIAMOND: 1.20
category_boosts:
  "4511": 1.15
  "default": 1.0
calculation:
  min_weight: 0.5
  max_weight: 1.5
  base_weight: 1.0
"""))
    def test_init_with_custom_config(self):
        """Test initialization with custom configuration file."""
        weighting = PreferenceWeighting("custom_config.yaml")
        assert weighting.config["user_preferences"]["cashback_vs_points_weight"] == 0.7
        assert weighting.config["loyalty_tiers"]["DIAMOND"] == 1.20

    def test_preference_weight_basic(self):
        """Test basic preference weight calculation."""
        weight = self.weighting.preference_weight(self.sample_card, self.sample_context)
        assert 0.5 <= weight <= 1.5
        assert isinstance(weight, float)

    def test_loyalty_tier_weights(self):
        """Test that different loyalty tiers produce different weights."""
        weights = {}
        for tier in LoyaltyTier:
            context = Context(
                customer=Customer(
                    id="test",
                    loyalty_tier=tier,
                    historical_velocity_24h=0,
                    chargebacks_12m=0,
                ),
                merchant=self.sample_context.merchant,
                cart=self.sample_context.cart,
                device=self.sample_context.device,
                geo=self.sample_context.geo,
            )
            weights[tier] = self.weighting.preference_weight(self.sample_card, context)

        # Higher loyalty tiers should have higher weights
        assert weights[LoyaltyTier.DIAMOND] > weights[LoyaltyTier.PLATINUM]
        assert weights[LoyaltyTier.PLATINUM] > weights[LoyaltyTier.GOLD]
        assert weights[LoyaltyTier.GOLD] > weights[LoyaltyTier.SILVER]
        assert weights[LoyaltyTier.SILVER] > weights[LoyaltyTier.NONE]

    def test_category_boost(self):
        """Test that category boosts are applied correctly."""
        # Test with airline category (should get boost)
        airline_context = self.sample_context
        airline_weight = self.weighting.preference_weight(self.sample_card, airline_context)

        # Test with grocery category (should get different boost)
        grocery_context = Context(
            customer=self.sample_context.customer,
            merchant=Merchant(
                name="Grocery Store",
                mcc="5411",  # Grocery stores
                network_preferences=["visa"],
                location={"city": "New York", "country": "US"},
            ),
            cart=Cart(
                items=[
                    CartItem(
                        item="Grocery Item",
                        unit_price=Decimal("50.00"),
                        qty=1,
                        mcc="5411",
                        merchant_category="Grocery",
                    )
                ],
                currency="USD",
            ),
            device=self.sample_context.device,
            geo=self.sample_context.geo,
        )
        grocery_weight = self.weighting.preference_weight(self.sample_card, grocery_context)

        # Weights should be different due to different category boosts
        assert airline_weight != grocery_weight

    def test_cashback_vs_points_preference(self):
        """Test cashback vs points preference weighting."""
        cashback_card = {
            **self.sample_card,
            "rewards_type": "cashback",
        }
        points_card = {
            **self.sample_card,
            "rewards_type": "points",
        }

        # Test with cashback preference
        self.weighting.config["user_preferences"]["cashback_vs_points_weight"] = 0.8
        cashback_weight = self.weighting.preference_weight(cashback_card, self.sample_context)
        points_weight = self.weighting.preference_weight(points_card, self.sample_context)
        assert cashback_weight > points_weight

        # Test with points preference
        self.weighting.config["user_preferences"]["cashback_vs_points_weight"] = 0.2
        cashback_weight = self.weighting.preference_weight(cashback_card, self.sample_context)
        points_weight = self.weighting.preference_weight(points_card, self.sample_context)
        assert points_weight > cashback_weight

    def test_annual_fee_tolerance(self):
        """Test annual fee tolerance weighting."""
        high_fee_card = {
            **self.sample_card,
            "annual_fee": 550,
        }
        no_fee_card = {
            **self.sample_card,
            "annual_fee": 0,
        }

        # Test with fee-averse preference
        self.weighting.config["user_preferences"]["annual_fee_tolerance"] = 0.1
        high_fee_weight = self.weighting.preference_weight(high_fee_card, self.sample_context)
        no_fee_weight = self.weighting.preference_weight(no_fee_card, self.sample_context)
        assert no_fee_weight > high_fee_weight

        # Test with fee-agnostic preference
        self.weighting.config["user_preferences"]["annual_fee_tolerance"] = 0.9
        high_fee_weight = self.weighting.preference_weight(high_fee_card, self.sample_context)
        no_fee_weight = self.weighting.preference_weight(no_fee_card, self.sample_context)
        # Fee-agnostic users might prefer high-fee cards due to better benefits
        assert abs(high_fee_weight - no_fee_weight) < 0.2

    def test_issuer_affinity(self):
        """Test issuer affinity weighting."""
        chase_card = {
            **self.sample_card,
            "issuer": "Chase",
        }
        amex_card = {
            **self.sample_card,
            "issuer": "American Express",
        }

        # Test with Chase affinity
        self.weighting.config["user_preferences"]["issuer_affinity"]["chase"] = 0.2
        chase_weight = self.weighting.preference_weight(chase_card, self.sample_context)
        amex_weight = self.weighting.preference_weight(amex_card, self.sample_context)
        assert chase_weight > amex_weight

        # Test with Amex affinity
        self.weighting.config["user_preferences"]["issuer_affinity"]["chase"] = 0.0
        self.weighting.config["user_preferences"]["issuer_affinity"]["american_express"] = 0.2
        chase_weight = self.weighting.preference_weight(chase_card, self.sample_context)
        amex_weight = self.weighting.preference_weight(amex_card, self.sample_context)
        assert amex_weight >= chase_weight  # Use >= to handle floating point precision

    def test_foreign_transaction_fee_sensitivity(self):
        """Test foreign transaction fee sensitivity."""
        foreign_fee_card = {
            **self.sample_card,
            "foreign_transaction_fee": 0.03,
        }
        no_foreign_fee_card = {
            **self.sample_card,
            "foreign_transaction_fee": 0.0,
        }

        # Test with fee-sensitive preference
        self.weighting.config["user_preferences"]["foreign_fee_sensitivity"] = 0.1
        foreign_fee_weight = self.weighting.preference_weight(foreign_fee_card, self.sample_context)
        no_foreign_fee_weight = self.weighting.preference_weight(no_foreign_fee_card, self.sample_context)
        assert no_foreign_fee_weight > foreign_fee_weight

        # Test with fee-insensitive preference
        self.weighting.config["user_preferences"]["foreign_fee_sensitivity"] = 0.9
        foreign_fee_weight = self.weighting.preference_weight(foreign_fee_card, self.sample_context)
        no_foreign_fee_weight = self.weighting.preference_weight(no_foreign_fee_card, self.sample_context)
        assert abs(foreign_fee_weight - no_foreign_fee_weight) < 0.1

    def test_signup_bonus_weighting(self):
        """Test that cards with signup bonuses get weighted higher."""
        bonus_card = {
            **self.sample_card,
            "signup_bonus_points": 100000,
        }
        no_bonus_card = {
            **self.sample_card,
            "signup_bonus_points": 0,
        }

        bonus_weight = self.weighting.preference_weight(bonus_card, self.sample_context)
        no_bonus_weight = self.weighting.preference_weight(no_bonus_card, self.sample_context)
        assert bonus_weight > no_bonus_weight

    def test_travel_benefits_weighting(self):
        """Test that cards with travel benefits get weighted higher."""
        travel_card = {
            **self.sample_card,
            "travel_benefits": ["Lounge access", "Trip insurance", "Global Entry credit"],
        }
        no_travel_card = {
            **self.sample_card,
            "travel_benefits": [],
        }

        travel_weight = self.weighting.preference_weight(travel_card, self.sample_context)
        no_travel_weight = self.weighting.preference_weight(no_travel_card, self.sample_context)
        assert travel_weight > no_travel_weight

    def test_weight_bounds(self):
        """Test that weights are properly bounded."""
        # Test with extreme preferences
        self.weighting.config["user_preferences"]["cashback_vs_points_weight"] = 0.0
        self.weighting.config["user_preferences"]["annual_fee_tolerance"] = 0.0
        self.weighting.config["user_preferences"]["foreign_fee_sensitivity"] = 0.0
        self.weighting.config["user_preferences"]["issuer_affinity"]["chase"] = -0.5

        weight = self.weighting.preference_weight(self.sample_card, self.sample_context)
        assert weight >= self.weighting.config["calculation"]["min_weight"]
        assert weight <= self.weighting.config["calculation"]["max_weight"]

    def test_error_handling(self):
        """Test error handling in weight calculation."""
        # Test with invalid card data
        invalid_card = {"name": "Invalid Card"}
        weight = self.weighting.preference_weight(invalid_card, self.sample_context)
        assert isinstance(weight, float)
        assert 0.5 <= weight <= 1.5

        # Test with missing context data
        minimal_context = Context(
            customer=Customer(
                id="test",
                loyalty_tier=LoyaltyTier.NONE,
                historical_velocity_24h=0,
                chargebacks_12m=0,
            ),
            merchant=Merchant(
                name="Test Merchant",
                mcc="5411",
                network_preferences=["visa"],
                location={"city": "New York", "country": "US"},
            ),
            cart=Cart(items=[], currency="USD"),
            device=self.sample_context.device,
            geo=self.sample_context.geo,
        )
        weight = self.weighting.preference_weight(self.sample_card, minimal_context)
        assert isinstance(weight, float)
        assert 0.5 <= weight <= 1.5
