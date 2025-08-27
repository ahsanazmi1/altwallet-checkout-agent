"""Tests for Merchant Penalty Module."""

import pytest
from decimal import Decimal
from unittest.mock import patch, mock_open

from src.altwallet_agent.merchant_penalty import MerchantPenalty
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


class TestMerchantPenalty:
    """Test cases for MerchantPenalty class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.penalty = MerchantPenalty()
        self.sample_context = Context(
            customer=Customer(
                id="test_customer",
                loyalty_tier=LoyaltyTier.GOLD,
                historical_velocity_24h=1,
                chargebacks_12m=0,
            ),
            merchant=Merchant(
                name="Amazon.com",
                mcc="5999",
                network_preferences=["visa", "mastercard"],
                location={"city": "Seattle", "country": "US"},
            ),
            cart=Cart(
                items=[
                    CartItem(
                        item="Test Item",
                        unit_price=Decimal("100.00"),
                        qty=1,
                        mcc="5999",
                        merchant_category="Online Retail",
                    )
                ],
                currency="USD",
            ),
            device=Device(
                ip="192.168.1.1",
                device_id="test_device_123",
                ip_distance_km=5.0,
                location={"city": "Seattle", "country": "US"},
            ),
            geo=Geo(
                city="Seattle",
                region="WA",
                country="US",
                lat=47.6062,
                lon=-122.3321,
            ),
        )

    def test_init_with_default_config(self):
        """Test initialization with default configuration."""
        penalty = MerchantPenalty()
        assert penalty.config is not None
        assert "merchants" in penalty.config
        assert "mcc_families" in penalty.config
        assert "network_penalties" in penalty.config

    @patch("builtins.open", mock_open(read_data="""
merchants:
  "amazon.com":
    "5999": 0.85
    "default": 0.90
  "walmart.com":
    "5311": 0.88
    "default": 0.92
mcc_families:
  "4511": 0.90
  "5411": 0.95
  "default": 1.0
network_penalties:
  debit_preference: 0.85
  visa_preference: 0.90
  default: 1.0
calculation:
  min_penalty: 0.8
  max_penalty: 1.0
  base_penalty: 1.0
  factor_weights:
    merchant_specific: 0.4
    mcc_family: 0.3
    network_preference: 0.3
"""))
    def test_init_with_custom_config(self):
        """Test initialization with custom configuration file."""
        penalty = MerchantPenalty("custom_config.yaml")
        assert penalty.config["merchants"]["amazon.com"]["5999"] == 0.85
        assert penalty.config["mcc_families"]["4511"] == 0.90

    def test_merchant_penalty_basic(self):
        """Test basic merchant penalty calculation."""
        penalty_value = self.penalty.merchant_penalty(self.sample_context)
        assert 0.8 <= penalty_value <= 1.0
        assert isinstance(penalty_value, float)

    def test_exact_merchant_match(self):
        """Test exact merchant name matching."""
        # Test with exact match
        context = Context(
            customer=self.sample_context.customer,
            merchant=Merchant(
                name="amazon.com",
                mcc="5999",
                network_preferences=["visa"],
                location={"city": "Seattle", "country": "US"},
            ),
            cart=self.sample_context.cart,
            device=self.sample_context.device,
            geo=self.sample_context.geo,
        )
        
        penalty_value = self.penalty.merchant_penalty(context)
        # Should get the exact penalty from config (0.85)
        assert penalty_value < 1.0

    def test_fuzzy_merchant_match(self):
        """Test fuzzy merchant name matching."""
        # Test with fuzzy match
        context = Context(
            customer=self.sample_context.customer,
            merchant=Merchant(
                name="amazon",  # Should match "amazon.com" via fuzzy matching
                mcc="5999",
                network_preferences=["visa"],
                location={"city": "Seattle", "country": "US"},
            ),
            cart=self.sample_context.cart,
            device=self.sample_context.device,
            geo=self.sample_context.geo,
        )
        
        penalty_value = self.penalty.merchant_penalty(context)
        # Should get a penalty due to fuzzy match
        assert penalty_value < 1.0

    def test_mcc_family_fallback(self):
        """Test MCC family fallback when no exact merchant match."""
        # Test with unknown merchant but known MCC
        context = Context(
            customer=self.sample_context.customer,
            merchant=Merchant(
                name="unknown_merchant",
                mcc="4511",  # Airlines MCC
                network_preferences=["visa"],
                location={"city": "New York", "country": "US"},
            ),
            cart=self.sample_context.cart,
            device=self.sample_context.device,
            geo=self.sample_context.geo,
        )
        
        penalty_value = self.penalty.merchant_penalty(context)
        # Should get MCC family penalty (0.90 for airlines)
        assert penalty_value < 1.0

    def test_network_preference_penalty(self):
        """Test network preference penalties."""
        # Test debit preference
        context = Context(
            customer=self.sample_context.customer,
            merchant=Merchant(
                name="test_merchant",
                mcc="5411",
                network_preferences=["debit"],
                location={"city": "New York", "country": "US"},
            ),
            cart=self.sample_context.cart,
            device=self.sample_context.device,
            geo=self.sample_context.geo,
        )
        
        penalty_value = self.penalty.merchant_penalty(context)
        # Should get debit preference penalty
        assert penalty_value < 1.0

        # Test Visa preference
        context.merchant.network_preferences = ["visa"]
        penalty_value = self.penalty.merchant_penalty(context)
        assert penalty_value < 1.0

        # Test Amex exclusion
        context.merchant.network_preferences = ["no_amex"]
        penalty_value = self.penalty.merchant_penalty(context)
        assert penalty_value < 1.0

    def test_no_data_fallback(self):
        """Test fallback to base penalty when no data is available."""
        # Test with completely unknown merchant and MCC
        context = Context(
            customer=self.sample_context.customer,
            merchant=Merchant(
                name="completely_unknown_merchant",
                mcc="9999",  # Unknown MCC
                network_preferences=[],
                location={"city": "New York", "country": "US"},
            ),
            cart=self.sample_context.cart,
            device=self.sample_context.device,
            geo=self.sample_context.geo,
        )
        
        penalty_value = self.penalty.merchant_penalty(context)
        # Should get base penalty (1.0)
        assert penalty_value == 1.0

    def test_merchant_name_normalization(self):
        """Test merchant name normalization."""
        # Test various merchant name formats
        test_cases = [
            ("Amazon.com", "amazon"),
            ("AMAZON.COM", "amazon"),
            ("Amazon-Store", "amazon-store"),
            ("Walmart.com", "walmart"),
            ("Target Store", "target store"),
        ]
        
        for input_name, expected_normalized in test_cases:
            normalized = self.penalty._normalize_merchant_name(input_name)
            assert normalized == expected_normalized

    def test_mcc_extraction(self):
        """Test MCC extraction from context."""
        # Test merchant MCC
        mcc = self.penalty._get_mcc_from_context(self.sample_context)
        assert mcc == "5999"

        # Test cart item MCC when merchant MCC is not available
        context = Context(
            customer=self.sample_context.customer,
            merchant=Merchant(
                name="test_merchant",
                mcc=None,  # No merchant MCC
                network_preferences=["visa"],
                location={"city": "New York", "country": "US"},
            ),
            cart=Cart(
                items=[
                    CartItem(
                        item="Test Item",
                        unit_price=Decimal("50.00"),
                        qty=1,
                        mcc="5411",  # Cart item MCC
                        merchant_category="Grocery",
                    )
                ],
                currency="USD",
            ),
            device=self.sample_context.device,
            geo=self.sample_context.geo,
        )
        
        mcc = self.penalty._get_mcc_from_context(context)
        assert mcc == "5411"

        # Test default when no MCC is available
        context.merchant.mcc = None
        context.cart.items[0].mcc = None
        mcc = self.penalty._get_mcc_from_context(context)
        assert mcc == "default"

    def test_fuzzy_matching(self):
        """Test fuzzy matching functionality."""
        # Test exact match
        match = self.penalty._find_fuzzy_merchant_match("amazon.com")
        assert match == "amazon.com"

        # Test variation match
        match = self.penalty._find_fuzzy_merchant_match("amzn")
        assert match is not None

        # Test no match
        match = self.penalty._find_fuzzy_merchant_match("completely_different")
        assert match is None

    def test_penalty_bounds(self):
        """Test that penalties are properly bounded."""
        # Test with extreme network preferences
        context = Context(
            customer=self.sample_context.customer,
            merchant=Merchant(
                name="test_merchant",
                mcc="4511",
                network_preferences=["no_visa", "no_mastercard"],  # Extreme preferences
                location={"city": "New York", "country": "US"},
            ),
            cart=self.sample_context.cart,
            device=self.sample_context.device,
            geo=self.sample_context.geo,
        )
        
        penalty_value = self.penalty.merchant_penalty(context)
        assert penalty_value >= self.penalty.config["calculation"]["min_penalty"]
        assert penalty_value <= self.penalty.config["calculation"]["max_penalty"]

    def test_error_handling(self):
        """Test error handling in penalty calculation."""
        # Test with invalid merchant name
        context = Context(
            customer=self.sample_context.customer,
            merchant=Merchant(
                name="",  # Empty merchant name
                mcc="5411",
                network_preferences=["visa"],
                location={"city": "New York", "country": "US"},
            ),
            cart=self.sample_context.cart,
            device=self.sample_context.device,
            geo=self.sample_context.geo,
        )
        
        penalty_value = self.penalty.merchant_penalty(context)
        assert isinstance(penalty_value, float)
        assert 0.8 <= penalty_value <= 1.0

    def test_different_merchants(self):
        """Test penalties for different merchant types."""
        merchants_to_test = [
            ("amazon.com", "5999", 0.85),  # Online retail
            ("walmart.com", "5311", 0.88),  # Department store
            ("delta.com", "4511", 0.88),    # Airline
            ("costco.com", "5411", 0.82),   # Warehouse club
        ]
        
        for merchant_name, mcc, expected_penalty in merchants_to_test:
            context = Context(
                customer=self.sample_context.customer,
                merchant=Merchant(
                    name=merchant_name,
                    mcc=mcc,
                    network_preferences=["visa"],
                    location={"city": "New York", "country": "US"},
                ),
                cart=self.sample_context.cart,
                device=self.sample_context.device,
                geo=self.sample_context.geo,
            )
            
            penalty_value = self.penalty.merchant_penalty(context)
            # Should be close to expected penalty (allowing for weighted combination)
            assert abs(penalty_value - expected_penalty) < 0.15

    def test_network_preference_combinations(self):
        """Test different network preference combinations."""
        test_cases = [
            (["debit"], "debit preference"),
            (["visa"], "visa preference"),
            (["mastercard"], "mastercard preference"),
            (["amex"], "amex preference"),
            (["discover"], "discover preference"),
            (["no_amex"], "amex exclusion"),
            (["no_visa"], "visa exclusion"),
            (["no_mastercard"], "mastercard exclusion"),
        ]
        
        for network_prefs, description in test_cases:
            context = Context(
                customer=self.sample_context.customer,
                merchant=Merchant(
                    name="test_merchant",
                    mcc="5411",
                    network_preferences=network_prefs,
                    location={"city": "New York", "country": "US"},
                ),
                cart=self.sample_context.cart,
                device=self.sample_context.device,
                geo=self.sample_context.geo,
            )
            
            penalty_value = self.penalty.merchant_penalty(context)
            assert isinstance(penalty_value, float)
            assert 0.8 <= penalty_value <= 1.0
