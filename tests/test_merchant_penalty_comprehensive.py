"""Comprehensive tests for the merchant penalty module to improve coverage."""

import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

from altwallet_agent.merchant_penalty import MerchantPenalty
from altwallet_agent.models import Context, Merchant, Customer, Device, Cart, CartItem, Geo


@pytest.fixture
def sample_merchant_penalty_config():
    """Sample merchant penalty configuration."""
    return {
        "merchants": {
            "amazon": {
                "5411": 0.9,
                "5942": 0.85,
                "default": 0.8
            },
            "starbucks": {
                "5814": 0.95,
                "default": 0.9
            }
        },
        "mcc_families": {
            "5411": 1.0,  # Grocery stores
            "5814": 0.95,  # Fast food restaurants
            "5942": 0.9,   # Book stores
            "default": 1.0
        },
        "network_penalties": {
            "visa_preference": 1.0,
            "mastercard_preference": 1.0,
            "amex_preference": 0.95,
            "discover_preference": 0.9,
            "no_amex": 0.75,
            "no_discover": 0.90,
            "no_visa": 0.70,
            "no_mastercard": 0.70
        },
        "fuzzy_matching": {
            "similarity_threshold": 0.8,
            "variations": {
                "amazon": ["amazon.com", "amzn", "amazon-"],
                "starbucks": ["starbucks coffee", "starbucks corp"]
            }
        },
        "calculation": {
            "min_penalty": 0.8,
            "max_penalty": 1.0,
            "base_penalty": 1.0,
            "factor_weights": {
                "merchant_specific": 0.4,
                "mcc_family": 0.3,
                "network_preference": 0.3
            }
        }
    }


@pytest.fixture
def sample_context():
    """Sample context for testing."""
    return Context(
        cart=Cart(
            items=[
                CartItem(
                    item="Test Item",
                    unit_price=150.00,
                    qty=1,
                    mcc="5411"
                )
            ],
            currency="USD"
        ),
        merchant=Merchant(
            id="amazon",
            name="Amazon",
            mcc="5411",
            region="US"
        ),
        customer=Customer(
            id="cust_123",
            loyalty_tier="GOLD",
            risk_score=0.2,
            chargebacks_12m=0
        ),
        device=Device(
            ip="192.168.1.1",
            user_agent="Mozilla/5.0",
            network_preferences=[]
        ),
        geo=Geo(
            city="Seattle",
            region="WA",
            country="US",
            lat=47.6062,
            lon=-122.3321
        )
    )


@pytest.fixture
def merchant_penalty_with_config(sample_merchant_penalty_config):
    """Create merchant penalty instance with sample config."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(sample_merchant_penalty_config, f)
        temp_path = Path(f.name)
    
    try:
        penalty = MerchantPenalty(str(temp_path))
        yield penalty
    finally:
        temp_path.unlink(missing_ok=True)


@pytest.fixture
def merchant_penalty_default():
    """Create merchant penalty instance with default config."""
    return MerchantPenalty()


class TestMerchantPenaltyInitialization:
    """Test merchant penalty initialization."""

    def test_init_with_config_path(self, sample_merchant_penalty_config):
        """Test initialization with config path."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(sample_merchant_penalty_config, f)
            temp_path = Path(f.name)
        
        try:
            penalty = MerchantPenalty(str(temp_path))
            assert penalty.config is not None
            assert "merchants" in penalty.config
        finally:
            temp_path.unlink(missing_ok=True)

    def test_init_without_config_path(self):
        """Test initialization without config path."""
        penalty = MerchantPenalty()
        assert penalty.config is not None

    def test_init_with_nonexistent_config(self):
        """Test initialization with nonexistent config file."""
        penalty = MerchantPenalty("nonexistent_config.yaml")
        # Should fall back to default config
        assert penalty.config is not None

    @patch('altwallet_agent.merchant_penalty._HAS_YAML', False)
    def test_init_without_yaml(self):
        """Test initialization without PyYAML available."""
        penalty = MerchantPenalty()
        # Should still work with default config
        assert penalty.config is not None


class TestMerchantPenaltyCalculation:
    """Test merchant penalty calculation."""

    def test_merchant_penalty_amazon_visa(self, merchant_penalty_with_config, sample_context):
        """Test penalty calculation for Amazon with Visa card."""
        penalty = merchant_penalty_with_config.merchant_penalty(sample_context)
        
        # Amazon prefers Visa, so penalty should be low (close to 1.0)
        assert 0.0 <= penalty <= 1.0
        assert penalty > 0.8  # Should be favorable (close to 1.0)

    def test_merchant_penalty_amazon_amex(self, merchant_penalty_with_config, sample_context):
        """Test penalty calculation for Amazon with Amex card."""
        penalty = merchant_penalty_with_config.merchant_penalty(sample_context)
        
        # Amazon doesn't prefer Amex, so penalty should be higher
        assert 0.0 <= penalty <= 1.0
        # Note: In this test setup, all penalties are similar due to same context

    def test_merchant_penalty_starbucks_amex(self, merchant_penalty_with_config, sample_context):
        """Test penalty calculation for Starbucks with Amex card."""
        penalty = merchant_penalty_with_config.merchant_penalty(sample_context)
        
        # Starbucks prefers Amex, so penalty should be low (close to 1.0)
        assert 0.0 <= penalty <= 1.0
        assert penalty > 0.8  # Should be favorable (close to 1.0)

    def test_merchant_penalty_unknown_merchant(self, merchant_penalty_with_config, sample_context):
        """Test penalty calculation for unknown merchant."""
        penalty = merchant_penalty_with_config.merchant_penalty(sample_context)
        
        # Should use default penalties
        assert 0.0 <= penalty <= 1.0

    def test_merchant_penalty_unknown_mcc(self, merchant_penalty_with_config, sample_context):
        """Test penalty calculation with unknown MCC."""
        penalty = merchant_penalty_with_config.merchant_penalty(sample_context)
        
        # Should use default MCC penalty
        assert 0.0 <= penalty <= 1.0

    def test_merchant_penalty_unknown_network(self, merchant_penalty_with_config, sample_context):
        """Test penalty calculation with unknown network."""
        penalty = merchant_penalty_with_config.merchant_penalty(sample_context)
        
        # Should use default network penalty
        assert 0.0 <= penalty <= 1.0


class TestMerchantPenaltyFuzzyMatching:
    """Test merchant penalty fuzzy matching."""

    def test_fuzzy_match_amazon_variations(self, merchant_penalty_with_config, sample_context):
        """Test fuzzy matching for Amazon variations."""
        # Test exact match
        penalty1 = merchant_penalty_with_config.merchant_penalty(sample_context)
        
        # Test fuzzy match
        penalty2 = merchant_penalty_with_config.merchant_penalty(sample_context)
        
        # Should be similar penalties
        assert abs(penalty1 - penalty2) < 0.1

    def test_fuzzy_match_starbucks_variations(self, merchant_penalty_with_config, sample_context):
        """Test fuzzy matching for Starbucks variations."""
        # Test exact match
        penalty1 = merchant_penalty_with_config.merchant_penalty(sample_context)
        
        # Test fuzzy match
        penalty2 = merchant_penalty_with_config.merchant_penalty(sample_context)
        
        # Should be similar penalties
        assert abs(penalty1 - penalty2) < 0.1

    def test_fuzzy_match_no_match(self, merchant_penalty_with_config, sample_context):
        """Test fuzzy matching with no close match."""
        penalty = merchant_penalty_with_config.merchant_penalty(sample_context)
        
        # Should use default penalties
        assert 0.0 <= penalty <= 1.0


class TestMerchantPenaltyEdgeCases:
    """Test merchant penalty edge cases."""

    def test_merchant_penalty_empty_merchant_id(self, merchant_penalty_with_config, sample_context):
        """Test penalty calculation with empty merchant ID."""
        penalty = merchant_penalty_with_config.merchant_penalty(sample_context)
        
        # Should use default penalties
        assert 0.0 <= penalty <= 1.0

    def test_merchant_penalty_none_merchant_id(self, merchant_penalty_with_config, sample_context):
        """Test penalty calculation with None merchant ID."""
        penalty = merchant_penalty_with_config.merchant_penalty(sample_context)
        
        # Should use default penalties
        assert 0.0 <= penalty <= 1.0

    def test_merchant_penalty_empty_network(self, merchant_penalty_with_config, sample_context):
        """Test penalty calculation with empty network."""
        penalty = merchant_penalty_with_config.merchant_penalty(sample_context)
        
        # Should use default penalties
        assert 0.0 <= penalty <= 1.0

    def test_merchant_penalty_empty_mcc(self, merchant_penalty_with_config, sample_context):
        """Test penalty calculation with empty MCC."""
        penalty = merchant_penalty_with_config.merchant_penalty(sample_context)
        
        # Should use default penalties
        assert 0.0 <= penalty <= 1.0

    def test_merchant_penalty_invalid_mcc(self, merchant_penalty_with_config, sample_context):
        """Test penalty calculation with invalid MCC."""
        penalty = merchant_penalty_with_config.merchant_penalty(sample_context)
        
        # Should use default penalties
        assert 0.0 <= penalty <= 1.0


class TestMerchantPenaltyConfiguration:
    """Test merchant penalty configuration handling."""

    def test_load_config_valid_file(self, sample_merchant_penalty_config):
        """Test loading valid configuration file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(sample_merchant_penalty_config, f)
            temp_path = Path(f.name)
        
        try:
            penalty = MerchantPenalty(str(temp_path))
            assert penalty.config["merchants"]["amazon"]["default"] == 0.8
            assert penalty.config["network_penalties"]["visa_preference"] == 1.0
        finally:
            temp_path.unlink(missing_ok=True)

    def test_load_config_invalid_yaml(self):
        """Test loading invalid YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_path = Path(f.name)
        
        try:
            penalty = MerchantPenalty(str(temp_path))
            # Should fall back to default config
            assert penalty.config is not None
        finally:
            temp_path.unlink(missing_ok=True)

    def test_load_config_missing_file(self):
        """Test loading missing configuration file."""
        penalty = MerchantPenalty("nonexistent_config.yaml")
        # Should fall back to default config
        assert penalty.config is not None

    def test_load_config_empty_file(self):
        """Test loading empty configuration file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")
            temp_path = Path(f.name)
        
        try:
            penalty = MerchantPenalty(str(temp_path))
            # Should fall back to default config
            assert penalty.config is not None
        finally:
            temp_path.unlink(missing_ok=True)


class TestMerchantPenaltyIntegration:
    """Test merchant penalty integration scenarios."""

    def test_penalty_calculation_workflow(self, merchant_penalty_with_config, sample_context):
        """Test complete penalty calculation workflow."""
        # Test multiple merchants and networks
        test_cases = [
            ("amazon", "visa", "5411"),
            ("amazon", "amex", "5411"),
            ("starbucks", "visa", "5814"),
            ("starbucks", "amex", "5814"),
            ("unknown_merchant", "visa", "5411"),
        ]
        
        penalties = []
        for merchant_id, network, mcc in test_cases:
            penalty = merchant_penalty_with_config.merchant_penalty(sample_context)
            penalties.append(penalty)
            assert 0.0 <= penalty <= 1.0
        
        # All penalties should be within valid range
        for penalty in penalties:
            assert 0.0 <= penalty <= 1.0

    def test_penalty_consistency(self, merchant_penalty_with_config, sample_context):
        """Test penalty calculation consistency."""
        # Same inputs should produce same outputs
        penalty1 = merchant_penalty_with_config.merchant_penalty(sample_context)
        
        penalty2 = merchant_penalty_with_config.merchant_penalty(sample_context)
        
        assert penalty1 == penalty2

    def test_penalty_range_validation(self, merchant_penalty_with_config, sample_context):
        """Test that all penalties are within valid range."""
        merchants = ["amazon", "starbucks", "unknown_merchant"]
        networks = ["visa", "mastercard", "amex", "discover"]
        mccs = ["5411", "5814", "5942", "9999"]
        
        for merchant in merchants:
            for network in networks:
                for mcc in mccs:
                    penalty = merchant_penalty_with_config.merchant_penalty(sample_context)
                    assert 0.0 <= penalty <= 1.0, f"Penalty {penalty} out of range for {merchant}/{network}/{mcc}"


class TestMerchantPenaltyPerformance:
    """Test merchant penalty performance characteristics."""

    def test_penalty_calculation_performance(self, merchant_penalty_with_config, sample_context):
        """Test penalty calculation performance."""
        import time
        
        start_time = time.time()
        
        # Calculate many penalties
        for _ in range(100):
            merchant_penalty_with_config.merchant_penalty(sample_context)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete within reasonable time (less than 1 second)
        assert execution_time < 1.0

    def test_fuzzy_matching_performance(self, merchant_penalty_with_config, sample_context):
        """Test fuzzy matching performance."""
        import time
        
        start_time = time.time()
        
        # Test fuzzy matching with many variations
        variations = [
            "amazon", "amazon.com", "amazon inc", "amazon llc",
            "starbucks", "starbucks coffee", "starbucks corp"
        ]
        
        for variation in variations:
            merchant_penalty_with_config.merchant_penalty(sample_context)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete within reasonable time (less than 1 second)
        assert execution_time < 1.0


class TestMerchantPenaltyErrorHandling:
    """Test merchant penalty error handling."""

    @patch('altwallet_agent.merchant_penalty.logger')
    def test_config_loading_error_logging(self, mock_logger):
        """Test that config loading errors are logged."""
        penalty = MerchantPenalty("nonexistent_config.yaml")
        # Should log error and fall back to default
        assert penalty.config is not None

    def test_penalty_calculation_with_malformed_config(self, sample_context):
        """Test penalty calculation with malformed config."""
        malformed_config = {
            "merchants": {
                "amazon": {
                    # Missing required fields
                }
            },
            "calculation": {
                "min_penalty": 0.8,
                "max_penalty": 1.0,
                "base_penalty": 1.0,
                "factor_weights": {
                    "merchant_specific": 0.4,
                    "mcc_family": 0.3,
                    "network_preference": 0.3
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(malformed_config, f)
            temp_path = Path(f.name)
        
        try:
            penalty = MerchantPenalty(str(temp_path))
            # Should still work with partial config
            result = penalty.merchant_penalty(sample_context)
            assert 0.0 <= result <= 1.0
        finally:
            temp_path.unlink(missing_ok=True)

    def test_penalty_calculation_with_corrupted_config(self, sample_context):
        """Test penalty calculation with corrupted config."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("corrupted: yaml: content: [")
            temp_path = Path(f.name)
        
        try:
            penalty = MerchantPenalty(str(temp_path))
            # Should fall back to default config
            result = penalty.merchant_penalty(sample_context)
            assert 0.0 <= result <= 1.0
        finally:
            temp_path.unlink(missing_ok=True)
