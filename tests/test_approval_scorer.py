"""Unit tests for ApprovalScorer module."""

import tempfile
from decimal import Decimal
from unittest.mock import patch

import pytest
import yaml

from src.altwallet_agent.approval_scorer import (
    ApprovalScorer,
    ApprovalResult,
    FeatureAttributions,
    AdditiveAttributions,
    FeatureContribution,
    LogisticCalibrator,
    IsotonicCalibrator,
)


class TestCalibrators:
    """Test calibration classes."""
    
    def test_logistic_calibrator_default(self):
        """Test logistic calibrator with default parameters."""
        calibrator = LogisticCalibrator()
        
        # Test edge cases
        assert calibrator.calibrate(0.0) == 0.5
        assert calibrator.calibrate(100.0) == pytest.approx(1.0, abs=1e-10)
        assert calibrator.calibrate(-100.0) == pytest.approx(0.0, abs=1e-10)
        
        # Test some intermediate values
        assert calibrator.calibrate(1.0) == pytest.approx(0.731, abs=0.001)
        assert calibrator.calibrate(-1.0) == pytest.approx(0.269, abs=0.001)
    
    def test_logistic_calibrator_custom_params(self):
        """Test logistic calibrator with custom bias and scale."""
        calibrator = LogisticCalibrator(bias=1.0, scale=2.0)
        
        # With bias=1.0, scale=2.0, raw_score=0 should give p=0.731
        assert calibrator.calibrate(0.0) == pytest.approx(0.731, abs=0.001)
        
        # raw_score=-0.5 should give p=0.5
        assert calibrator.calibrate(-0.5) == pytest.approx(0.5, abs=0.001)
    
    def test_isotonic_calibrator_placeholder(self):
        """Test isotonic calibrator placeholder implementation."""
        calibrator = IsotonicCalibrator(bias=0.0, scale=1.0)
        
        # Should behave like logistic for now
        assert calibrator.calibrate(0.0) == 0.5
        assert calibrator.calibrate(1.0) == pytest.approx(0.731, abs=0.001)


class TestApprovalScorer:
    """Test ApprovalScorer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.scorer = ApprovalScorer()
    
    def test_init_with_default_config(self):
        """Test initialization with default configuration."""
        scorer = ApprovalScorer()
        assert scorer.config is not None
        assert "rules_layer" in scorer.config
        assert "calibration_layer" in scorer.config
        assert "output" in scorer.config
    
    def test_init_with_custom_config(self):
        """Test initialization with custom configuration file."""
        # Create a temporary config file
        config_data = {
            "rules_layer": {
                "mcc_weights": {"test": 1.0, "default": 0.0},
                "amount_weights": {"0-100": 0.5},
                "issuer_family_weights": {"visa": 0.1},
                "cross_border_weight": -2.0,
                "location_mismatch_weights": {"0-10": 0.0},
                "velocity_weights": {
                    "24h": {"0-10": 0.0},
                    "7d": {"0-50": 0.0}
                },
                "chargeback_weights": {"0": 0.0},
                "merchant_risk_weights": {"low": 0.5},
                "loyalty_weights": {"GOLD": 1.0},
                "base_score": 0.5
            },
            "calibration_layer": {
                "method": "logistic",
                "logistic": {"bias": 0.0, "scale": 1.0}
            },
            "output": {
                "min_probability": 0.05,
                "max_probability": 0.95,
                "random_seed": 123
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            scorer = ApprovalScorer(config_path)
            assert scorer.config["rules_layer"]["mcc_weights"]["test"] == 1.0
            assert scorer.config["output"]["min_probability"] == 0.05
        finally:
            import os
            os.unlink(config_path)
    
    def test_score_typical_case(self):
        """Test scoring with typical transaction data."""
        context = {
            "mcc": "5411",  # Grocery store
            "amount": Decimal("50.00"),
            "issuer_family": "visa",
            "cross_border": False,
            "location_mismatch_distance": 0.0,
            "velocity_24h": 3,
            "velocity_7d": 15,
            "chargebacks_12m": 0,
            "merchant_risk_tier": "low",
            "loyalty_tier": "GOLD"
        }
        
        result = self.scorer.score(context)
        
        assert isinstance(result, ApprovalResult)
        assert 0.0 <= result.p_approval <= 1.0
        assert isinstance(result.raw_score, float)
        assert result.calibration["method"] == "logistic"
        assert result.attributions is not None
        assert result.additive_attributions is not None
        
        # Test additive attributions structure
        additive_attribs = result.additive_attributions
        assert hasattr(additive_attribs, 'baseline')
        assert hasattr(additive_attribs, 'contribs')
        assert hasattr(additive_attribs, 'sum')
        assert isinstance(additive_attribs.contribs, list)
        
        # Test additivity
        contrib_sum = sum(contrib.value for contrib in additive_attribs.contribs)
        total_sum = contrib_sum + additive_attribs.baseline
        assert abs(total_sum - additive_attribs.sum) <= 1e-10
        assert abs(total_sum - result.raw_score) <= 1e-10
    
    def test_score_high_risk_case(self):
        """Test scoring with high-risk transaction data."""
        context = {
            "mcc": "7995",  # Gambling
            "amount": Decimal("2000.00"),
            "issuer_family": "unknown",
            "cross_border": True,
            "location_mismatch_distance": 200.0,
            "velocity_24h": 25,
            "velocity_7d": 150,
            "chargebacks_12m": 3,
            "merchant_risk_tier": "high",
            "loyalty_tier": "NONE"
        }
        
        result = self.scorer.score(context)
        
        # Should have lower approval probability
        assert result.p_approval < 0.5
        assert result.raw_score < 0.0
    
    def test_score_low_risk_case(self):
        """Test scoring with low-risk transaction data."""
        context = {
            "mcc": "5411",  # Grocery store
            "amount": Decimal("25.00"),
            "issuer_family": "visa",
            "cross_border": False,
            "location_mismatch_distance": 0.0,
            "velocity_24h": 2,
            "velocity_7d": 8,
            "chargebacks_12m": 0,
            "merchant_risk_tier": "low",
            "loyalty_tier": "PLATINUM"
        }
        
        result = self.scorer.score(context)
        
        # Should have higher approval probability
        assert result.p_approval > 0.5
        assert result.raw_score > 0.0
    
    def test_score_missing_fields(self):
        """Test scoring with missing fields (should use defaults)."""
        context = {
            "amount": Decimal("100.00")
            # All other fields missing
        }
        
        result = self.scorer.score(context)
        
        assert isinstance(result, ApprovalResult)
        assert 0.0 <= result.p_approval <= 1.0
        assert result.attributions is not None
    
    def test_score_empty_context(self):
        """Test scoring with empty context."""
        context = {}
        
        result = self.scorer.score(context)
        
        assert isinstance(result, ApprovalResult)
        assert 0.0 <= result.p_approval <= 1.0
    
    def test_probability_clamping(self):
        """Test that probabilities are clamped to configured bounds."""
        # Create a scorer with tight bounds
        config_data = {
            "rules_layer": {
                "mcc_weights": {"default": 0.0},
                "amount_weights": {"0-100": 0.0},
                "issuer_family_weights": {"unknown": 0.0},
                "cross_border_weight": 0.0,
                "location_mismatch_weights": {"0-10": 0.0},
                "velocity_weights": {
                    "24h": {"0-10": 0.0},
                    "7d": {"0-50": 0.0}
                },
                "chargeback_weights": {"0": 0.0},
                "merchant_risk_weights": {"unknown": 0.0},
                "loyalty_weights": {"NONE": 0.0},
                "base_score": 0.0
            },
            "calibration_layer": {
                "method": "logistic",
                "logistic": {"bias": 0.0, "scale": 1.0}
            },
            "output": {
                "min_probability": 0.1,
                "max_probability": 0.9,
                "random_seed": 42
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            scorer = ApprovalScorer(config_path)
            
            # Test very high raw score (should be clamped to 0.9)
            with patch.object(scorer.calibrator, 'calibrate', return_value=0.99):
                result = scorer.score({"amount": Decimal("100.00")})
                assert result.p_approval == 0.9
            
            # Test very low raw score (should be clamped to 0.1)
            with patch.object(scorer.calibrator, 'calibrate', return_value=0.01):
                result = scorer.score({"amount": Decimal("100.00")})
                assert result.p_approval == 0.1
        finally:
            import os
            os.unlink(config_path)
    
    def test_deterministic_behavior(self):
        """Test that scoring is deterministic with same input."""
        context = {
            "mcc": "5411",
            "amount": Decimal("100.00"),
            "issuer_family": "visa",
            "cross_border": False,
            "location_mismatch_distance": 0.0,
            "velocity_24h": 5,
            "velocity_7d": 20,
            "chargebacks_12m": 0,
            "merchant_risk_tier": "medium",
            "loyalty_tier": "SILVER"
        }
        
        result1 = self.scorer.score(context)
        result2 = self.scorer.score(context)
        
        assert result1.p_approval == result2.p_approval
        assert result1.raw_score == result2.raw_score
    
    def test_explain_method(self):
        """Test the explain method returns additive attributions."""
        context = {
            "mcc": "5411",
            "amount": Decimal("100.00"),
            "issuer_family": "visa",
            "cross_border": False,
            "location_mismatch_distance": 0.0,
            "velocity_24h": 5,
            "velocity_7d": 20,
            "chargebacks_12m": 0,
            "merchant_risk_tier": "medium",
            "loyalty_tier": "SILVER"
        }
        
        attributions = self.scorer.explain(context)
        
        assert isinstance(attributions, AdditiveAttributions)
        assert hasattr(attributions, 'baseline')
        assert hasattr(attributions, 'contribs')
        assert hasattr(attributions, 'sum')
        
        # Check that contribs is a list of FeatureContribution objects
        assert isinstance(attributions.contribs, list)
        for contrib in attributions.contribs:
            assert isinstance(contrib, FeatureContribution)
            assert hasattr(contrib, 'feature')
            assert hasattr(contrib, 'value')
    
    def test_amount_weight_ranges(self):
        """Test amount weight calculation for different ranges."""
        # Test small amount
        context_small = {"amount": Decimal("5.00")}
        result_small = self.scorer.score(context_small)
        
        # Test medium amount
        context_medium = {"amount": Decimal("500.00")}
        result_medium = self.scorer.score(context_medium)
        
        # Test large amount
        context_large = {"amount": Decimal("5000.00")}
        result_large = self.scorer.score(context_large)
        
        # Large amounts should generally have lower approval odds
        assert result_large.p_approval <= result_medium.p_approval
        assert result_medium.p_approval <= result_small.p_approval
    
    def test_velocity_weight_ranges(self):
        """Test velocity weight calculation for different ranges."""
        # Test low velocity
        context_low = {"velocity_24h": 2, "velocity_7d": 10}
        result_low = self.scorer.score(context_low)
        
        # Test high velocity
        context_high = {"velocity_24h": 30, "velocity_7d": 200}
        result_high = self.scorer.score(context_high)
        
        # High velocity should generally have lower approval odds
        assert result_high.p_approval <= result_low.p_approval
    
    def test_chargeback_weight_ranges(self):
        """Test chargeback weight calculation for different ranges."""
        # Test no chargebacks
        context_none = {"chargebacks_12m": 0}
        result_none = self.scorer.score(context_none)
        
        # Test some chargebacks
        context_some = {"chargebacks_12m": 2}
        result_some = self.scorer.score(context_some)
        
        # Test many chargebacks
        context_many = {"chargebacks_12m": 5}
        result_many = self.scorer.score(context_many)
        
        # More chargebacks should generally have lower approval odds
        assert result_many.p_approval <= result_some.p_approval
        assert result_some.p_approval <= result_none.p_approval
    
    def test_loyalty_tier_weights(self):
        """Test loyalty tier weight calculation."""
        # Test no loyalty
        context_none = {"loyalty_tier": "NONE"}
        result_none = self.scorer.score(context_none)
        
        # Test gold loyalty
        context_gold = {"loyalty_tier": "GOLD"}
        result_gold = self.scorer.score(context_gold)
        
        # Test platinum loyalty
        context_platinum = {"loyalty_tier": "PLATINUM"}
        result_platinum = self.scorer.score(context_platinum)
        
        # Higher loyalty tiers should generally have higher approval odds
        assert result_platinum.p_approval >= result_gold.p_approval
        assert result_gold.p_approval >= result_none.p_approval
    
    def test_merchant_risk_weights(self):
        """Test merchant risk tier weight calculation."""
        # Test low risk merchant
        context_low = {"merchant_risk_tier": "low"}
        result_low = self.scorer.score(context_low)
        
        # Test high risk merchant
        context_high = {"merchant_risk_tier": "high"}
        result_high = self.scorer.score(context_high)
        
        # High risk merchants should generally have lower approval odds
        assert result_high.p_approval <= result_low.p_approval
    
    def test_cross_border_flag(self):
        """Test cross-border flag impact."""
        # Test domestic transaction
        context_domestic = {"cross_border": False}
        result_domestic = self.scorer.score(context_domestic)
        
        # Test cross-border transaction
        context_cross_border = {"cross_border": True}
        result_cross_border = self.scorer.score(context_cross_border)
        
        # Cross-border transactions should generally have lower approval odds
        assert result_cross_border.p_approval <= result_domestic.p_approval
    
    def test_location_mismatch_impact(self):
        """Test location mismatch distance impact."""
        # Test no mismatch
        context_no_mismatch = {"location_mismatch_distance": 0.0}
        result_no_mismatch = self.scorer.score(context_no_mismatch)
        
        # Test small mismatch
        context_small_mismatch = {"location_mismatch_distance": 25.0}
        result_small_mismatch = self.scorer.score(context_small_mismatch)
        
        # Test large mismatch
        context_large_mismatch = {"location_mismatch_distance": 300.0}
        result_large_mismatch = self.scorer.score(context_large_mismatch)
        
        # Larger mismatches should generally have lower approval odds
        assert result_large_mismatch.p_approval <= result_small_mismatch.p_approval
        assert result_small_mismatch.p_approval <= result_no_mismatch.p_approval


class TestMonotonicity:
    """Test monotonicity - more risk factors should lead to lower approval probabilities."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.scorer = ApprovalScorer()
    
    def test_mcc_risk_monotonicity(self):
        """Test that higher-risk MCCs lead to lower approval probabilities."""
        base_context = {
            "amount": Decimal("100.00"),
            "issuer_family": "visa",
            "cross_border": False,
            "location_mismatch_distance": 0.0,
            "velocity_24h": 1,
            "velocity_7d": 5,
            "chargebacks_12m": 0,
            "merchant_risk_tier": "low",
            "loyalty_tier": "GOLD"
        }
        
        # Test MCC risk progression: low-risk -> medium-risk -> high-risk -> extremely high-risk
        mcc_test_cases = [
            ("5411", "low_risk"),      # Grocery store
            ("5541", "medium_risk"),   # Gas station
            ("7994", "high_risk"),     # Video game arcades
            ("7995", "extremely_high_risk")  # Gambling
        ]
        
        results = []
        for mcc, risk_level in mcc_test_cases:
            context = base_context.copy()
            context["mcc"] = mcc
            result = self.scorer.score(context)
            results.append((risk_level, result.p_approval))
        
        # Verify monotonicity: each higher risk level should have lower approval probability
        for i in range(1, len(results)):
            assert results[i][1] <= results[i-1][1], \
                f"Risk level {results[i][0]} should have lower approval probability than {results[i-1][0]}"
    
    def test_amount_risk_monotonicity(self):
        """Test that larger amounts lead to lower approval probabilities."""
        base_context = {
            "mcc": "5411",  # Grocery store
            "issuer_family": "visa",
            "cross_border": False,
            "location_mismatch_distance": 0.0,
            "velocity_24h": 1,
            "velocity_7d": 5,
            "chargebacks_12m": 0,
            "merchant_risk_tier": "low",
            "loyalty_tier": "GOLD"
        }
        
        # Test amount risk progression
        amount_test_cases = [
            (Decimal("5.00"), "very_small"),
            (Decimal("50.00"), "small"),
            (Decimal("500.00"), "medium"),
            (Decimal("5000.00"), "large"),
            (Decimal("25000.00"), "very_large")
        ]
        
        results = []
        for amount, size in amount_test_cases:
            context = base_context.copy()
            context["amount"] = amount
            result = self.scorer.score(context)
            results.append((size, result.p_approval))
        
        # Verify monotonicity: each larger amount should have lower approval probability
        for i in range(1, len(results)):
            assert results[i][1] <= results[i-1][1], \
                f"Amount size {results[i][0]} should have lower approval probability than {results[i-1][0]}"
    
    def test_geo_distance_monotonicity(self):
        """Test that larger geo distances lead to lower approval probabilities."""
        base_context = {
            "mcc": "5411",  # Grocery store
            "amount": Decimal("100.00"),
            "issuer_family": "visa",
            "cross_border": False,
            "velocity_24h": 1,
            "velocity_7d": 5,
            "chargebacks_12m": 0,
            "merchant_risk_tier": "low",
            "loyalty_tier": "GOLD"
        }
        
        # Test geo distance risk progression
        distance_test_cases = [
            (0.0, "same_city"),
            (25.0, "same_metro"),
            (100.0, "same_state"),
            (500.0, "same_country"),
            (5000.0, "different_continent")
        ]
        
        results = []
        for distance, location in distance_test_cases:
            context = base_context.copy()
            context["location_mismatch_distance"] = distance
            result = self.scorer.score(context)
            results.append((location, result.p_approval))
        
        # Verify monotonicity: each larger distance should have lower approval probability
        for i in range(1, len(results)):
            assert results[i][1] <= results[i-1][1], \
                f"Distance {results[i][0]} should have lower approval probability than {results[i-1][0]}"
    
    def test_cross_border_risk_impact(self):
        """Test that cross-border transactions have significantly lower approval probabilities."""
        base_context = {
            "mcc": "5411",  # Grocery store
            "amount": Decimal("100.00"),
            "issuer_family": "visa",
            "location_mismatch_distance": 0.0,
            "velocity_24h": 1,
            "velocity_7d": 5,
            "chargebacks_12m": 0,
            "merchant_risk_tier": "low",
            "loyalty_tier": "GOLD"
        }
        
        # Test domestic vs cross-border
        context_domestic = base_context.copy()
        context_domestic["cross_border"] = False
        result_domestic = self.scorer.score(context_domestic)
        
        context_cross_border = base_context.copy()
        context_cross_border["cross_border"] = True
        result_cross_border = self.scorer.score(context_cross_border)
        
        # Cross-border should have significantly lower approval probability
        assert result_cross_border.p_approval < result_domestic.p_approval
        # The difference should be substantial (at least 10% lower)
        assert result_domestic.p_approval - result_cross_border.p_approval > 0.1
    
    def test_combined_risk_factors_monotonicity(self):
        """Test that adding multiple risk factors leads to monotonically decreasing approval probabilities."""
        base_context = {
            "mcc": "5411",  # Grocery store
            "amount": Decimal("100.00"),
            "issuer_family": "visa",
            "cross_border": False,
            "location_mismatch_distance": 0.0,
            "velocity_24h": 1,
            "velocity_7d": 5,
            "chargebacks_12m": 0,
            "merchant_risk_tier": "low",
            "loyalty_tier": "GOLD"
        }
        
        # Start with base context
        result_base = self.scorer.score(base_context)
        results = [("base", result_base.p_approval)]
        
        # Add risk factor 1: medium-risk MCC (less extreme than gambling)
        context_1 = base_context.copy()
        context_1["mcc"] = "5541"  # Gas station
        result_1 = self.scorer.score(context_1)
        results.append(("medium_risk_mcc", result_1.p_approval))
        
        # Add risk factor 2: larger amount
        context_2 = context_1.copy()
        context_2["amount"] = Decimal("1000.00")
        result_2 = self.scorer.score(context_2)
        results.append(("larger_amount", result_2.p_approval))
        
        # Add risk factor 3: cross-border
        context_3 = context_2.copy()
        context_3["cross_border"] = True
        result_3 = self.scorer.score(context_3)
        results.append(("cross_border", result_3.p_approval))
        
        # Add risk factor 4: geo distance
        context_4 = context_3.copy()
        context_4["location_mismatch_distance"] = 1000.0
        result_4 = self.scorer.score(context_4)
        results.append(("geo_distance", result_4.p_approval))
        
        # Verify monotonicity: each additional risk factor should decrease approval probability
        for i in range(1, len(results)):
            assert results[i][1] <= results[i-1][1], \
                f"Adding risk factor {results[i][0]} should not increase approval probability from {results[i-1][0]}"
    
    def test_extreme_risk_scenarios(self):
        """Test extreme risk scenarios that should result in very low approval probabilities."""
        # Extremely high-risk scenario
        extreme_context = {
            "mcc": "7995",  # Gambling
            "amount": Decimal("50000.00"),  # Very large amount
            "issuer_family": "unknown",
            "cross_border": True,
            "location_mismatch_distance": 15000.0,  # Extreme distance
            "velocity_24h": 100,
            "velocity_7d": 1000,
            "chargebacks_12m": 10,
            "merchant_risk_tier": "high",
            "loyalty_tier": "NONE"
        }
        
        result = self.scorer.score(extreme_context)
        
        # Should have very low approval probability
        assert result.p_approval < 0.1, f"Extreme risk scenario should have very low approval probability, got {result.p_approval}"
        assert result.raw_score < -5.0, f"Extreme risk scenario should have very negative raw score, got {result.raw_score}"
    
    def test_missing_fields_defaults(self):
        """Test that missing fields use sensible defaults that maintain risk monotonicity."""
        # Test with all fields missing (should use conservative defaults)
        empty_context = {}
        result_empty = self.scorer.score(empty_context)
        
        # Test with only amount provided (should be more favorable than empty)
        amount_only_context = {"amount": Decimal("5.00")}  # Very small amount
        result_amount_only = self.scorer.score(amount_only_context)
        
        # Test with low-risk context (should be more favorable than amount-only)
        low_risk_context = {
            "mcc": "5411",  # Grocery store
            "amount": Decimal("5.00"),  # Very small amount
            "issuer_family": "visa",
            "cross_border": False,
            "location_mismatch_distance": 0.0,
            "velocity_24h": 1,
            "velocity_7d": 5,
            "chargebacks_12m": 0,
            "merchant_risk_tier": "low",
            "loyalty_tier": "GOLD"
        }
        result_low_risk = self.scorer.score(low_risk_context)
        
        # Verify that all scenarios produce valid probabilities
        assert 0.0 <= result_empty.p_approval <= 1.0
        assert 0.0 <= result_amount_only.p_approval <= 1.0
        assert 0.0 <= result_low_risk.p_approval <= 1.0
        
        # Verify that low-risk context has higher approval probability than amount-only
        assert result_low_risk.p_approval >= result_amount_only.p_approval


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_invalid_config_file(self):
        """Test handling of invalid configuration file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            config_path = f.name
        
        try:
            # Should not raise exception, should use defaults
            scorer = ApprovalScorer(config_path)
            assert scorer.config is not None
        finally:
            import os
            os.unlink(config_path)
    
    def test_nonexistent_config_file(self):
        """Test handling of nonexistent configuration file."""
        # Should not raise exception, should use defaults
        scorer = ApprovalScorer("nonexistent_config.yaml")
        assert scorer.config is not None
    
    def test_extreme_amount_values(self):
        """Test scoring with extreme amount values."""
        scorer = ApprovalScorer()
        
        # Test very small amount
        context_small = {"amount": Decimal("0.01")}
        result_small = scorer.score(context_small)
        assert 0.0 <= result_small.p_approval <= 1.0
        
        # Test very large amount
        context_large = {"amount": Decimal("1000000.00")}
        result_large = scorer.score(context_large)
        assert 0.0 <= result_large.p_approval <= 1.0
    
    def test_extreme_velocity_values(self):
        """Test scoring with extreme velocity values."""
        scorer = ApprovalScorer()
        
        # Test very high velocity
        context_high = {"velocity_24h": 1000, "velocity_7d": 10000}
        result_high = scorer.score(context_high)
        assert 0.0 <= result_high.p_approval <= 1.0
        
        # Test negative velocity (should be handled gracefully)
        context_negative = {"velocity_24h": -5, "velocity_7d": -10}
        result_negative = scorer.score(context_negative)
        assert 0.0 <= result_negative.p_approval <= 1.0
    
    def test_unknown_mcc(self):
        """Test scoring with unknown MCC code."""
        scorer = ApprovalScorer()
        
        context = {"mcc": "9999"}  # Unknown MCC
        result = scorer.score(context)
        
        # Should use default weight and not crash
        assert 0.0 <= result.p_approval <= 1.0
    
    def test_unknown_issuer_family(self):
        """Test scoring with unknown issuer family."""
        scorer = ApprovalScorer()
        
        context = {"issuer_family": "unknown_issuer"}
        result = scorer.score(context)
        
        # Should use default weight and not crash
        assert 0.0 <= result.p_approval <= 1.0
    
    def test_unknown_merchant_risk_tier(self):
        """Test scoring with unknown merchant risk tier."""
        scorer = ApprovalScorer()
        
        context = {"merchant_risk_tier": "unknown_tier"}
        result = scorer.score(context)
        
        # Should use default weight and not crash
        assert 0.0 <= result.p_approval <= 1.0
    
    def test_unknown_loyalty_tier(self):
        """Test scoring with unknown loyalty tier."""
        scorer = ApprovalScorer()
        
        context = {"loyalty_tier": "UNKNOWN_TIER"}
        result = scorer.score(context)
        
        # Should use default weight and not crash
        assert 0.0 <= result.p_approval <= 1.0
