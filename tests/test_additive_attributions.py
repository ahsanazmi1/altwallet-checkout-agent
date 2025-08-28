"""Tests for Additive Feature Attributions."""

from decimal import Decimal

from altwallet_agent.approval_scorer import (
    AdditiveAttributions,
    ApprovalScorer,
    FeatureContribution,
)


class TestAdditiveAttributions:
    """Test cases for additive feature attributions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.scorer = ApprovalScorer()

    def test_additive_attributions_structure(self):
        """Test that additive attributions have the correct structure."""
        context = {
            "mcc": "5411",
            "amount": Decimal("100.00"),
            "issuer_family": "visa",
            "cross_border": False,
            "location_mismatch_distance": 0.0,
            "velocity_24h": 5,
            "velocity_7d": 20,
            "chargebacks_12m": 0,
            "merchant_risk_tier": "low",
            "loyalty_tier": "GOLD",
        }

        result = self.scorer.score(context)

        assert result.additive_attributions is not None
        assert hasattr(result.additive_attributions, "baseline")
        assert hasattr(result.additive_attributions, "contribs")
        assert hasattr(result.additive_attributions, "sum")

        # Check that contribs is a list of FeatureContribution objects
        assert isinstance(result.additive_attributions.contribs, list)
        for contrib in result.additive_attributions.contribs:
            assert isinstance(contrib, FeatureContribution)
            assert hasattr(contrib, "feature")
            assert hasattr(contrib, "value")

    def test_additivity_validation(self):
        """Test that contributions sum to the raw score within epsilon."""
        context = {
            "mcc": "5411",
            "amount": Decimal("50.00"),
            "issuer_family": "visa",
            "cross_border": False,
            "location_mismatch_distance": 0.0,
            "velocity_24h": 2,
            "velocity_7d": 8,
            "chargebacks_12m": 0,
            "merchant_risk_tier": "low",
            "loyalty_tier": "PLATINUM",
        }

        result = self.scorer.score(context)
        additive_attribs = result.additive_attributions

        # Calculate sum of contributions + baseline
        contrib_sum = sum(contrib.value for contrib in additive_attribs.contribs)
        total_sum = contrib_sum + additive_attribs.baseline

        # Should match the sum field within epsilon
        epsilon = 1e-10
        assert abs(total_sum - additive_attribs.sum) <= epsilon
        assert abs(total_sum - result.raw_score) <= epsilon

    def test_feature_contribution_values(self):
        """Test that feature contributions have reasonable values."""
        context = {
            "mcc": "7995",  # Gambling (high risk)
            "amount": Decimal("1000.00"),  # High amount
            "issuer_family": "unknown",  # Unknown issuer
            "cross_border": True,  # Cross-border transaction
            "location_mismatch_distance": 200.0,  # High distance
            "velocity_24h": 25,  # High velocity
            "velocity_7d": 150,  # High velocity
            "chargebacks_12m": 3,  # High chargebacks
            "merchant_risk_tier": "high",  # High risk merchant
            "loyalty_tier": "NONE",  # No loyalty
        }

        result = self.scorer.score(context)
        additive_attribs = result.additive_attributions

        # Check that we have contributions
        assert len(additive_attribs.contribs) > 0

        # Check that each contribution has a feature name and value
        valid_features = [
            "mcc",
            "amount",
            "issuer_family",
            "cross_border",
            "location_mismatch",
            "velocity_24h",
            "velocity_7d",
            "chargebacks_12m",
            "merchant_risk",
            "loyalty_tier",
        ]
        for contrib in additive_attribs.contribs:
            assert contrib.feature in valid_features
            assert isinstance(contrib.value, (int, float))

    def test_zero_contributions_excluded(self):
        """Test that zero contributions are excluded from the list."""
        context = {
            "mcc": "5411",
            "amount": Decimal("100.00"),
            "issuer_family": "visa",
            "cross_border": False,  # Should be 0 contribution
            "location_mismatch_distance": 0.0,  # Should be 0 contribution
            "velocity_24h": 0,  # Should be 0 contribution
            "velocity_7d": 0,  # Should be 0 contribution
            "chargebacks_12m": 0,  # Should be 0 contribution
            "merchant_risk_tier": "low",
            "loyalty_tier": "GOLD",
        }

        result = self.scorer.score(context)
        additive_attribs = result.additive_attributions

        # Check that zero contributions are not included
        for contrib in additive_attribs.contribs:
            assert abs(contrib.value) > 1e-10

    def test_explain_method_returns_additive_attributions(self):
        """Test that explain method returns additive attributions."""
        context = {
            "mcc": "5411",
            "amount": Decimal("100.00"),
            "issuer_family": "visa",
            "cross_border": False,
            "location_mismatch_distance": 0.0,
            "velocity_24h": 5,
            "velocity_7d": 20,
            "chargebacks_12m": 0,
            "merchant_risk_tier": "low",
            "loyalty_tier": "GOLD",
        }

        additive_attribs = self.scorer.explain(context)

        assert isinstance(additive_attribs, AdditiveAttributions)
        assert hasattr(additive_attribs, "baseline")
        assert hasattr(additive_attribs, "contribs")
        assert hasattr(additive_attribs, "sum")

    def test_top_drivers_extraction(self):
        """Test extraction of top positive and negative drivers."""
        context = {
            "mcc": "7995",  # High risk (negative)
            "amount": Decimal("1000.00"),  # High amount (negative)
            "issuer_family": "visa",  # Positive
            "cross_border": True,  # Negative
            "location_mismatch_distance": 200.0,  # Negative
            "velocity_24h": 25,  # Negative
            "velocity_7d": 150,  # Negative
            "chargebacks_12m": 3,  # Negative
            "merchant_risk_tier": "high",  # Negative
            "loyalty_tier": "PLATINUM",  # Positive
        }

        result = self.scorer.score(context)
        additive_attribs = result.additive_attributions

        # Extract top drivers
        top_drivers = self.scorer._extract_top_drivers(additive_attribs, top_k=3)

        assert "top_positive" in top_drivers
        assert "top_negative" in top_drivers

        # Check that positive drivers have positive values
        for contrib in top_drivers["top_positive"]:
            assert contrib.value > 0

        # Check that negative drivers have negative values
        for contrib in top_drivers["top_negative"]:
            assert contrib.value < 0

        # Check that we don't have more than top_k drivers
        assert len(top_drivers["top_positive"]) <= 3
        assert len(top_drivers["top_negative"]) <= 3

    def test_top_drivers_ordering(self):
        """Test that top drivers are ordered by absolute value."""
        context = {
            "mcc": "7995",  # High risk
            "amount": Decimal("1000.00"),  # High amount
            "issuer_family": "visa",
            "cross_border": True,
            "location_mismatch_distance": 200.0,
            "velocity_24h": 25,
            "velocity_7d": 150,
            "chargebacks_12m": 3,
            "merchant_risk_tier": "high",
            "loyalty_tier": "PLATINUM",
        }

        result = self.scorer.score(context)
        additive_attribs = result.additive_attributions

        # Extract top drivers
        top_drivers = self.scorer._extract_top_drivers(additive_attribs, top_k=5)

        # Check that positive drivers are ordered by absolute value (descending)
        positive_values = [
            abs(contrib.value) for contrib in top_drivers["top_positive"]
        ]
        assert positive_values == sorted(positive_values, reverse=True)

        # Check that negative drivers are ordered by absolute value (descending)
        negative_values = [
            abs(contrib.value) for contrib in top_drivers["top_negative"]
        ]
        assert negative_values == sorted(negative_values, reverse=True)

    def test_baseline_contribution(self):
        """Test that baseline contribution is included in the sum."""
        context = {
            "mcc": "5411",
            "amount": Decimal("100.00"),
            "issuer_family": "visa",
            "cross_border": False,
            "location_mismatch_distance": 0.0,
            "velocity_24h": 5,
            "velocity_7d": 20,
            "chargebacks_12m": 0,
            "merchant_risk_tier": "low",
            "loyalty_tier": "GOLD",
        }

        result = self.scorer.score(context)
        additive_attribs = result.additive_attributions

        # Baseline should be included in the sum
        contrib_sum = sum(contrib.value for contrib in additive_attribs.contribs)
        total_sum = contrib_sum + additive_attribs.baseline

        assert abs(total_sum - additive_attribs.sum) <= 1e-10

    def test_edge_case_empty_context(self):
        """Test additive attributions with minimal context."""
        context = {
            "amount": Decimal("100.00")
            # All other fields missing
        }

        result = self.scorer.score(context)
        additive_attribs = result.additive_attributions

        # Should still have valid structure
        assert additive_attribs.baseline is not None
        assert isinstance(additive_attribs.contribs, list)
        assert additive_attribs.sum is not None

        # Additivity should still hold
        contrib_sum = sum(contrib.value for contrib in additive_attribs.contribs)
        total_sum = contrib_sum + additive_attribs.baseline
        assert abs(total_sum - additive_attribs.sum) <= 1e-10

    def test_high_risk_vs_low_risk_comparison(self):
        """Test that high-risk and low-risk transactions have different attribution patterns."""
        # Low-risk context
        low_risk_context = {
            "mcc": "5411",  # Grocery store
            "amount": Decimal("25.00"),
            "issuer_family": "visa",
            "cross_border": False,
            "location_mismatch_distance": 0.0,
            "velocity_24h": 2,
            "velocity_7d": 8,
            "chargebacks_12m": 0,
            "merchant_risk_tier": "low",
            "loyalty_tier": "PLATINUM",
        }

        # High-risk context
        high_risk_context = {
            "mcc": "7995",  # Gambling
            "amount": Decimal("2000.00"),
            "issuer_family": "unknown",
            "cross_border": True,
            "location_mismatch_distance": 200.0,
            "velocity_24h": 25,
            "velocity_7d": 150,
            "chargebacks_12m": 3,
            "merchant_risk_tier": "high",
            "loyalty_tier": "NONE",
        }

        low_risk_result = self.scorer.score(low_risk_context)
        high_risk_result = self.scorer.score(high_risk_context)

        low_risk_attribs = low_risk_result.additive_attributions
        high_risk_attribs = high_risk_result.additive_attributions

        # High-risk should have lower raw score
        assert high_risk_attribs.sum < low_risk_attribs.sum

        # High-risk should have more negative contributions
        high_risk_negative_count = sum(
            1 for c in high_risk_attribs.contribs if c.value < 0
        )
        low_risk_negative_count = sum(
            1 for c in low_risk_attribs.contribs if c.value < 0
        )

        assert high_risk_negative_count >= low_risk_negative_count

    def test_additive_attributions_json_serializable(self):
        """Test that additive attributions can be serialized to JSON."""
        context = {
            "mcc": "5411",
            "amount": Decimal("100.00"),
            "issuer_family": "visa",
            "cross_border": False,
            "location_mismatch_distance": 0.0,
            "velocity_24h": 5,
            "velocity_7d": 20,
            "chargebacks_12m": 0,
            "merchant_risk_tier": "low",
            "loyalty_tier": "GOLD",
        }

        result = self.scorer.score(context)
        additive_attribs = result.additive_attributions

        # Should be JSON serializable
        import json

        json_str = json.dumps(additive_attribs.dict())
        assert isinstance(json_str, str)

        # Should be able to reconstruct
        reconstructed = AdditiveAttributions(**json.loads(json_str))
        assert reconstructed.baseline == additive_attribs.baseline
        assert len(reconstructed.contribs) == len(additive_attribs.contribs)
        assert reconstructed.sum == additive_attribs.sum
