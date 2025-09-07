"""Comprehensive tests for Preference & Loyalty Weighting Module."""

import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import mock_open, patch, MagicMock

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
from altwallet_agent.preference_weighting import PreferenceWeighting


class TestPreferenceWeightingInitialization:
    """Test PreferenceWeighting initialization and configuration loading."""

    def test_init_with_config_path(self):
        """Test initialization with custom config path."""
        config_content = """
user_preferences:
  cashback_vs_points_weight: 0.7
  issuer_affinity:
    chase: 0.1
    american_express: 0.2
  annual_fee_tolerance: 0.6
  foreign_fee_sensitivity: 0.8
loyalty_tiers:
  NONE: 1.0
  SILVER: 1.05
  GOLD: 1.10
category_boosts:
  "4511": 1.15
  "5812": 1.10
  default: 1.0
calculation:
  min_weight: 0.5
  max_weight: 1.5
  base_weight: 1.0
"""
        
        with patch("builtins.open", mock_open(read_data=config_content)):
            with patch("yaml.safe_load", return_value={
                "user_preferences": {
                    "cashback_vs_points_weight": 0.7,
                    "issuer_affinity": {"chase": 0.1, "american_express": 0.2},
                    "annual_fee_tolerance": 0.6,
                    "foreign_fee_sensitivity": 0.8
                },
                "loyalty_tiers": {"NONE": 1.0, "SILVER": 1.05, "GOLD": 1.10},
                "category_boosts": {"4511": 1.15, "5812": 1.10, "default": 1.0},
                "calculation": {"min_weight": 0.5, "max_weight": 1.5, "base_weight": 1.0}
            }):
                weighting = PreferenceWeighting("custom_config.yaml")
                
                assert weighting.config["user_preferences"]["cashback_vs_points_weight"] == 0.7
                assert weighting.config["user_preferences"]["issuer_affinity"]["chase"] == 0.1

    def test_init_without_yaml(self):
        """Test initialization when PyYAML is not available."""
        with patch("altwallet_agent.preference_weighting._HAS_YAML", False):
            weighting = PreferenceWeighting()
            
            # Should use default config
            assert "user_preferences" in weighting.config
            assert "loyalty_tiers" in weighting.config
            assert "category_boosts" in weighting.config
            assert "calculation" in weighting.config

    def test_init_with_nonexistent_config(self):
        """Test initialization with nonexistent config file."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            weighting = PreferenceWeighting("nonexistent.yaml")
            
            # Should fall back to default config
            assert "user_preferences" in weighting.config
            assert weighting.config["calculation"]["base_weight"] == 1.0

    def test_init_with_invalid_yaml(self):
        """Test initialization with invalid YAML file."""
        with patch("builtins.open", mock_open(read_data="invalid: yaml: content: [")):
            with patch("yaml.safe_load", side_effect=Exception("Invalid YAML")):
                weighting = PreferenceWeighting("invalid.yaml")
                
                # Should fall back to default config
                assert "user_preferences" in weighting.config

    def test_init_with_non_dict_config(self):
        """Test initialization with config that's not a dictionary."""
        with patch("builtins.open", mock_open(read_data="not a dict")):
            with patch("yaml.safe_load", return_value="not a dictionary"):
                weighting = PreferenceWeighting("non_dict.yaml")
                
                # Should fall back to default config
                assert isinstance(weighting.config, dict)


class TestPreferenceWeightingCalculation:
    """Test preference weight calculation methods."""

    @pytest.fixture
    def sample_context(self):
        """Sample context for testing."""
        return Context(
            cart=Cart(
                items=[
                    CartItem(
                        item="Test Item",
                        unit_price=Decimal("100.00"),
                        qty=1,
                        mcc="4511"
                    )
                ],
                currency="USD"
            ),
            merchant=Merchant(
                id="test_merchant",
                name="Test Merchant",
                mcc="4511",
                region="US"
            ),
            customer=Customer(
                id="test_customer",
                loyalty_tier=LoyaltyTier.GOLD,
                risk_score=0.2,
                chargebacks_12m=0
            ),
            device=Device(
                ip="192.168.1.1",
                user_agent="Mozilla/5.0",
                network_preferences=[]
            ),
            geo=Geo(
                city="New York",
                region="NY",
                country="US",
                lat=40.7128,
                lon=-74.0060
            )
        )

    @pytest.fixture
    def sample_card(self):
        """Sample card for testing."""
        return {
            "name": "Test Card",
            "issuer": "chase",
            "annual_fee": 95,
            "rewards_type": "points",
            "signup_bonus_points": 50000,
            "category_bonuses": {"travel": 0.03},
            "travel_benefits": ["Trip insurance"],
            "foreign_transaction_fee": 0.0,
        }

    def test_preference_weight_basic(self, sample_card, sample_context):
        """Test basic preference weight calculation."""
        weighting = PreferenceWeighting()
        weight = weighting.preference_weight(sample_card, sample_context)
        
        assert isinstance(weight, float)
        assert 0.5 <= weight <= 1.5

    def test_preference_weight_with_error(self, sample_context):
        """Test preference weight calculation with invalid card data."""
        weighting = PreferenceWeighting()
        invalid_card = {"name": "Invalid Card"}  # Missing required fields
        
        weight = weighting.preference_weight(invalid_card, sample_context)
        
        # Should return a valid weight (not necessarily 1.0 due to other factors)
        assert isinstance(weight, float)
        assert 0.5 <= weight <= 1.5

    def test_preference_weight_with_invalid_config(self, sample_card, sample_context):
        """Test preference weight with invalid config values."""
        weighting = PreferenceWeighting()
        # Corrupt the config
        weighting.config["calculation"]["base_weight"] = "invalid"
        weighting.config["calculation"]["min_weight"] = "invalid"
        weighting.config["calculation"]["max_weight"] = "invalid"
        
        weight = weighting.preference_weight(sample_card, sample_context)
        
        # Should still return a valid weight
        assert isinstance(weight, float)
        assert 0.5 <= weight <= 1.5

    def test_calculate_user_preference_weight_cashback_preference(self, sample_context):
        """Test user preference weight with cashback preference."""
        weighting = PreferenceWeighting()
        weighting.config["user_preferences"]["cashback_vs_points_weight"] = 0.8  # Prefer cashback
        
        cashback_card = {
            "name": "Cashback Card",
            "issuer": "chase",
            "rewards_type": "cashback",
            "annual_fee": 0,
            "foreign_transaction_fee": 0
        }
        
        weight = weighting._calculate_user_preference_weight(cashback_card, sample_context)
        assert weight > 1.0  # Should get boost for cashback preference

    def test_calculate_user_preference_weight_points_preference(self, sample_context):
        """Test user preference weight with points preference."""
        weighting = PreferenceWeighting()
        weighting.config["user_preferences"]["cashback_vs_points_weight"] = 0.2  # Prefer points
        
        points_card = {
            "name": "Points Card",
            "issuer": "chase",
            "rewards_type": "points",
            "annual_fee": 0,
            "foreign_transaction_fee": 0
        }
        
        weight = weighting._calculate_user_preference_weight(points_card, sample_context)
        assert weight > 1.0  # Should get boost for points preference

    def test_calculate_user_preference_weight_issuer_affinity(self, sample_context):
        """Test user preference weight with issuer affinity."""
        weighting = PreferenceWeighting()
        weighting.config["user_preferences"]["issuer_affinity"]["chase"] = 0.2
        
        chase_card = {
            "name": "Chase Card",
            "issuer": "chase",
            "rewards_type": "cashback",
            "annual_fee": 0,
            "foreign_transaction_fee": 0
        }
        
        weight = weighting._calculate_user_preference_weight(chase_card, sample_context)
        assert weight > 1.0  # Should get boost for issuer affinity

    def test_calculate_user_preference_weight_annual_fee_averse(self, sample_context):
        """Test user preference weight with fee-averse user."""
        weighting = PreferenceWeighting()
        weighting.config["user_preferences"]["annual_fee_tolerance"] = 0.2  # Fee-averse
        
        expensive_card = {
            "name": "Expensive Card",
            "issuer": "chase",
            "rewards_type": "cashback",
            "annual_fee": 500,
            "foreign_transaction_fee": 0
        }
        
        weight = weighting._calculate_user_preference_weight(expensive_card, sample_context)
        assert weight < 1.0  # Should get penalty for high fee

    def test_calculate_user_preference_weight_annual_fee_agnostic(self, sample_context):
        """Test user preference weight with fee-agnostic user."""
        weighting = PreferenceWeighting()
        weighting.config["user_preferences"]["annual_fee_tolerance"] = 0.8  # Fee-agnostic
        
        expensive_card = {
            "name": "Expensive Card",
            "issuer": "chase",
            "rewards_type": "cashback",
            "annual_fee": 500,
            "foreign_transaction_fee": 0
        }
        
        weight = weighting._calculate_user_preference_weight(expensive_card, sample_context)
        assert weight > 1.0  # Should get boost for being fee-agnostic

    def test_calculate_user_preference_weight_foreign_fee_sensitive(self, sample_context):
        """Test user preference weight with foreign fee sensitivity."""
        weighting = PreferenceWeighting()
        weighting.config["user_preferences"]["foreign_fee_sensitivity"] = 0.3  # Fee-sensitive
        
        foreign_fee_card = {
            "name": "Foreign Fee Card",
            "issuer": "chase",
            "rewards_type": "cashback",
            "annual_fee": 0,
            "foreign_transaction_fee": 0.03
        }
        
        weight = weighting._calculate_user_preference_weight(foreign_fee_card, sample_context)
        assert weight < 1.0  # Should get penalty for foreign fee

    def test_calculate_user_preference_weight_invalid_config_values(self, sample_context):
        """Test user preference weight with invalid config values."""
        weighting = PreferenceWeighting()
        weighting.config["user_preferences"]["cashback_vs_points_weight"] = "invalid"
        weighting.config["user_preferences"]["issuer_affinity"]["chase"] = "invalid"
        weighting.config["user_preferences"]["annual_fee_tolerance"] = "invalid"
        weighting.config["user_preferences"]["foreign_fee_sensitivity"] = "invalid"
        
        card = {
            "name": "Test Card",
            "issuer": "chase",
            "rewards_type": "cashback",
            "annual_fee": 0,
            "foreign_transaction_fee": 0
        }
        
        weight = weighting._calculate_user_preference_weight(card, sample_context)
        assert weight == 1.0  # Should use defaults

    def test_calculate_loyalty_weight_different_tiers(self, sample_context):
        """Test loyalty weight calculation for different tiers."""
        weighting = PreferenceWeighting()
        
        # Test different loyalty tiers
        tiers = [LoyaltyTier.NONE, LoyaltyTier.SILVER, LoyaltyTier.GOLD, LoyaltyTier.PLATINUM, LoyaltyTier.DIAMOND]
        expected_weights = [1.0, 1.05, 1.10, 1.15, 1.20]
        
        for tier, expected_weight in zip(tiers, expected_weights):
            sample_context.customer.loyalty_tier = tier
            weight = weighting._calculate_loyalty_weight(sample_context)
            assert weight == expected_weight

    def test_calculate_loyalty_weight_invalid_config(self, sample_context):
        """Test loyalty weight with invalid config."""
        weighting = PreferenceWeighting()
        weighting.config["loyalty_tiers"]["GOLD"] = "invalid"
        
        weight = weighting._calculate_loyalty_weight(sample_context)
        assert weight == 1.0  # Should use default

    def test_calculate_category_weight_with_mcc_match(self, sample_card, sample_context):
        """Test category weight with MCC that matches card bonuses."""
        weighting = PreferenceWeighting()
        
        # Card has travel bonus, context has airline MCC
        weight = weighting._calculate_category_weight(sample_card, sample_context)
        assert weight > 1.0  # Should get boost

    def test_calculate_category_weight_without_mcc_match(self, sample_context):
        """Test category weight without MCC match."""
        weighting = PreferenceWeighting()
        
        card = {
            "name": "No Bonus Card",
            "category_bonuses": {}
        }
        
        weight = weighting._calculate_category_weight(card, sample_context)
        assert weight == 1.15  # Should get MCC boost

    def test_calculate_category_weight_no_mcc(self, sample_card):
        """Test category weight with no MCC in context."""
        weighting = PreferenceWeighting()
        
        context = Context(
            cart=Cart(items=[], currency="USD"),
            merchant=Merchant(id="test", name="Test", mcc=None, region="US"),
            customer=Customer(id="test", loyalty_tier=LoyaltyTier.NONE, risk_score=0.2, chargebacks_12m=0),
            device=Device(ip="192.168.1.1", user_agent="Mozilla/5.0", network_preferences=[]),
            geo=Geo(city="NYC", region="NY", country="US", lat=40.7128, lon=-74.0060)
        )
        
        weight = weighting._calculate_category_weight(sample_card, context)
        assert weight == 1.0  # Should use default

    def test_calculate_category_weight_invalid_config(self, sample_card, sample_context):
        """Test category weight with invalid config."""
        weighting = PreferenceWeighting()
        weighting.config["category_boosts"]["4511"] = "invalid"
        weighting.config["category_boosts"]["default"] = "invalid"
        
        weight = weighting._calculate_category_weight(sample_card, sample_context)
        # Should still get some boost due to category bonus match
        assert weight >= 1.0

    def test_calculate_promotion_weight_with_signup_bonus(self, sample_context):
        """Test promotion weight with signup bonus."""
        weighting = PreferenceWeighting()
        
        card = {
            "name": "Bonus Card",
            "signup_bonus_points": 100000
        }
        
        weight = weighting._calculate_promotion_weight(card, sample_context)
        assert weight > 1.0  # Should get boost for signup bonus

    def test_calculate_promotion_weight_with_travel_benefits(self, sample_context):
        """Test promotion weight with travel benefits."""
        weighting = PreferenceWeighting()
        
        card = {
            "name": "Travel Card",
            "travel_benefits": ["Lounge access", "Trip insurance"]
        }
        
        weight = weighting._calculate_promotion_weight(card, sample_context)
        assert weight > 1.0  # Should get boost for travel benefits

    def test_calculate_promotion_weight_with_seasonal_promotion(self, sample_context):
        """Test promotion weight with active seasonal promotion."""
        weighting = PreferenceWeighting()
        weighting.config["seasonal_promotions"] = {
            "holiday_bonus": {
                "start_date": "01-01",
                "end_date": "12-31",
                "affected_categories": ["4511"],
                "multiplier": 1.2
            }
        }
        
        card = {"name": "Promo Card"}
        
        weight = weighting._calculate_promotion_weight(card, sample_context)
        assert weight > 1.0  # Should get boost from seasonal promotion

    def test_calculate_promotion_weight_inactive_seasonal_promotion(self, sample_context):
        """Test promotion weight with inactive seasonal promotion."""
        weighting = PreferenceWeighting()
        weighting.config["seasonal_promotions"] = {
            "holiday_bonus": {
                "start_date": "01-01",
                "end_date": "01-02",  # Very short period
                "affected_categories": ["4511"],
                "multiplier": 1.2
            }
        }
        
        # Mock current date to be outside the promotion period
        with patch("altwallet_agent.preference_weighting.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 6, 15)  # Mid-year
            
            card = {"name": "Promo Card"}
            weight = weighting._calculate_promotion_weight(card, sample_context)
            assert weight == 1.0  # Should not get boost from inactive promotion


class TestPreferenceWeightingPromotionHelpers:
    """Test promotion helper methods."""

    def test_is_promotion_active_within_year(self):
        """Test promotion active check within same year."""
        weighting = PreferenceWeighting()
        
        promotion_data = {
            "start_date": "06-01",
            "end_date": "08-31"
        }
        
        # Test dates within the promotion period
        current_date = datetime(2024, 7, 15)
        assert weighting._is_promotion_active(promotion_data, current_date) is True
        
        # Test dates outside the promotion period
        current_date = datetime(2024, 9, 15)
        assert weighting._is_promotion_active(promotion_data, current_date) is False

    def test_is_promotion_active_cross_year(self):
        """Test promotion active check across year boundary."""
        weighting = PreferenceWeighting()
        
        promotion_data = {
            "start_date": "12-01",
            "end_date": "02-28"
        }
        
        # Test dates within the cross-year promotion period
        current_date = datetime(2024, 12, 15)
        assert weighting._is_promotion_active(promotion_data, current_date) is True
        
        current_date = datetime(2025, 1, 15)
        assert weighting._is_promotion_active(promotion_data, current_date) is True
        
        current_date = datetime(2025, 2, 15)
        assert weighting._is_promotion_active(promotion_data, current_date) is True
        
        # Test dates outside the promotion period
        current_date = datetime(2024, 11, 15)
        assert weighting._is_promotion_active(promotion_data, current_date) is False
        
        current_date = datetime(2025, 3, 15)
        assert weighting._is_promotion_active(promotion_data, current_date) is False

    def test_is_promotion_active_invalid_dates(self):
        """Test promotion active check with invalid dates."""
        weighting = PreferenceWeighting()
        
        # Test with missing dates
        promotion_data = {}
        current_date = datetime(2024, 7, 15)
        assert weighting._is_promotion_active(promotion_data, current_date) is False
        
        # Test with invalid date format
        promotion_data = {
            "start_date": "invalid",
            "end_date": "08-31"
        }
        assert weighting._is_promotion_active(promotion_data, current_date) is False

    def test_is_category_affected_with_merchant_mcc(self):
        """Test category affected check with merchant MCC."""
        weighting = PreferenceWeighting()
        
        context = Context(
            cart=Cart(items=[], currency="USD"),
            merchant=Merchant(id="test", name="Test", mcc="4511", region="US"),
            customer=Customer(id="test", loyalty_tier=LoyaltyTier.NONE, risk_score=0.2, chargebacks_12m=0),
            device=Device(ip="192.168.1.1", user_agent="Mozilla/5.0", network_preferences=[]),
            geo=Geo(city="NYC", region="NY", country="US", lat=40.7128, lon=-74.0060)
        )
        
        affected_categories = ["4511", "5812"]
        assert weighting._is_category_affected(affected_categories, context) is True
        
        affected_categories = ["5812", "5411"]
        assert weighting._is_category_affected(affected_categories, context) is False

    def test_is_category_affected_with_cart_mcc(self):
        """Test category affected check with cart item MCC."""
        weighting = PreferenceWeighting()
        
        context = Context(
            cart=Cart(
                items=[
                    CartItem(
                        item="Test Item",
                        unit_price=Decimal("100.00"),
                        qty=1,
                        mcc="5812"
                    )
                ],
                currency="USD"
            ),
            merchant=Merchant(id="test", name="Test", mcc=None, region="US"),
            customer=Customer(id="test", loyalty_tier=LoyaltyTier.NONE, risk_score=0.2, chargebacks_12m=0),
            device=Device(ip="192.168.1.1", user_agent="Mozilla/5.0", network_preferences=[]),
            geo=Geo(city="NYC", region="NY", country="US", lat=40.7128, lon=-74.0060)
        )
        
        affected_categories = ["4511", "5812"]
        assert weighting._is_category_affected(affected_categories, context) is True

    def test_is_category_affected_no_mcc(self):
        """Test category affected check with no MCC."""
        weighting = PreferenceWeighting()
        
        context = Context(
            cart=Cart(items=[], currency="USD"),
            merchant=Merchant(id="test", name="Test", mcc=None, region="US"),
            customer=Customer(id="test", loyalty_tier=LoyaltyTier.NONE, risk_score=0.2, chargebacks_12m=0),
            device=Device(ip="192.168.1.1", user_agent="Mozilla/5.0", network_preferences=[]),
            geo=Geo(city="NYC", region="NY", country="US", lat=40.7128, lon=-74.0060)
        )
        
        affected_categories = ["4511", "5812"]
        assert weighting._is_category_affected(affected_categories, context) is False


class TestPreferenceWeightingEdgeCases:
    """Test edge cases and error handling."""

    def test_preference_weight_with_missing_card_fields(self):
        """Test preference weight with missing card fields."""
        weighting = PreferenceWeighting()
        
        context = Context(
            cart=Cart(items=[], currency="USD"),
            merchant=Merchant(id="test", name="Test", mcc="4511", region="US"),
            customer=Customer(id="test", loyalty_tier=LoyaltyTier.NONE, risk_score=0.2, chargebacks_12m=0),
            device=Device(ip="192.168.1.1", user_agent="Mozilla/5.0", network_preferences=[]),
            geo=Geo(city="NYC", region="NY", country="US", lat=40.7128, lon=-74.0060)
        )
        
        # Card with minimal fields
        minimal_card = {"name": "Minimal Card"}
        
        weight = weighting.preference_weight(minimal_card, context)
        assert isinstance(weight, float)
        assert 0.5 <= weight <= 1.5

    def test_preference_weight_with_empty_context(self):
        """Test preference weight with minimal context."""
        weighting = PreferenceWeighting()
        
        context = Context(
            cart=Cart(items=[], currency="USD"),
            merchant=Merchant(id="test", name="Test", mcc=None, region="US"),
            customer=Customer(id="test", loyalty_tier=LoyaltyTier.NONE, risk_score=0.2, chargebacks_12m=0),
            device=Device(ip="192.168.1.1", user_agent="Mozilla/5.0", network_preferences=[]),
            geo=Geo(city="NYC", region="NY", country="US", lat=40.7128, lon=-74.0060)
        )
        
        card = {"name": "Test Card", "issuer": "chase"}
        
        weight = weighting.preference_weight(card, context)
        assert isinstance(weight, float)
        assert 0.5 <= weight <= 1.5

    def test_preference_weight_bounds_enforcement(self):
        """Test that preference weights are properly bounded."""
        weighting = PreferenceWeighting()
        
        context = Context(
            cart=Cart(items=[], currency="USD"),
            merchant=Merchant(id="test", name="Test", mcc="4511", region="US"),
            customer=Customer(id="test", loyalty_tier=LoyaltyTier.DIAMOND, risk_score=0.2, chargebacks_12m=0),
            device=Device(ip="192.168.1.1", user_agent="Mozilla/5.0", network_preferences=[]),
            geo=Geo(city="NYC", region="NY", country="US", lat=40.7128, lon=-74.0060)
        )
        
        # Card that should maximize weight
        max_card = {
            "name": "Max Card",
            "issuer": "chase",
            "rewards_type": "cashback",
            "annual_fee": 0,
            "foreign_transaction_fee": 0,
            "signup_bonus_points": 100000,
            "travel_benefits": ["Lounge access"],
            "category_bonuses": {"travel": 0.05}
        }
        
        weight = weighting.preference_weight(max_card, context)
        assert weight <= 1.5  # Should be bounded by max_weight
        
        # Card that should minimize weight
        min_card = {
            "name": "Min Card",
            "issuer": "unknown",
            "rewards_type": "points",
            "annual_fee": 1000,
            "foreign_transaction_fee": 0.05
        }
        
        weight = weighting.preference_weight(min_card, context)
        assert weight >= 0.5  # Should be bounded by min_weight
