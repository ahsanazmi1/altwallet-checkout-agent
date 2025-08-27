"""Tests for Enhanced Recommendations with Explainability and Audit."""

from decimal import Decimal

from altwallet_agent.core import CheckoutAgent
from altwallet_agent.models import CheckoutRequest, EnhancedCheckoutResponse


class TestEnhancedRecommendations:
    """Test cases for enhanced recommendations functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.agent = CheckoutAgent()

    def test_enhanced_recommendations_structure(self):
        """Test that enhanced recommendations have the correct structure."""
        request = CheckoutRequest(
            merchant_id="test_merchant",
            amount=Decimal("100.00"),
            currency="USD",
            cart={
                "items": [
                    {
                        "item": "Test Item",
                        "unit_price": "100.00",
                        "qty": 1,
                        "mcc": "5411"
                    }
                ],
                "currency": "USD"
            },
            merchant={
                "name": "Test Merchant",
                "mcc": "5411",
                "network_preferences": ["visa"],
                "location": {"city": "Test City", "country": "US"}
            },
            customer={
                "id": "test_customer",
                "loyalty_tier": "GOLD",
                "historical_velocity_24h": 2,
                "chargebacks_12m": 0
            },
            device={
                "ip": "192.168.1.1",
                "device_id": "test_device",
                "location": {"city": "Test City", "country": "US"}
            },
            geo={"city": "Test City", "country": "US"}
        )

        response = self.agent.process_checkout_enhanced(request)

        # Verify response structure
        assert isinstance(response, EnhancedCheckoutResponse)
        assert response.transaction_id is not None
        assert response.score >= 0.0 and response.score <= 1.0
        assert response.status == "completed"
        assert len(response.recommendations) > 0

        # Verify each recommendation structure
        for rec in response.recommendations:
            assert rec.card_id is not None
            assert rec.card_name is not None
            assert rec.rank > 0
            assert rec.p_approval >= 0.0 and rec.p_approval <= 1.0
            assert rec.expected_rewards >= 0.0
            assert rec.utility >= 0.0 and rec.utility <= 1.0

            # Verify explainability structure
            assert "baseline" in rec.explainability
            assert "contributions" in rec.explainability
            assert "calibration" in rec.explainability
            assert "top_drivers" in rec.explainability
            assert "positive" in rec.explainability["top_drivers"]
            assert "negative" in rec.explainability["top_drivers"]

            # Verify audit structure
            assert "config_versions" in rec.audit
            assert "code_version" in rec.audit
            assert "request_id" in rec.audit
            assert "latency_ms" in rec.audit
            assert rec.audit["latency_ms"] >= 0

    def test_explainability_contributions(self):
        """Test that explainability contributions are valid."""
        request = CheckoutRequest(
            merchant_id="test_merchant",
            amount=Decimal("50.00"),
            currency="USD",
            cart={
                "items": [
                    {
                        "item": "Test Item",
                        "unit_price": "50.00",
                        "qty": 1,
                        "mcc": "5411"
                    }
                ],
                "currency": "USD"
            },
            merchant={
                "name": "Test Merchant",
                "mcc": "5411",
                "network_preferences": ["visa"],
                "location": {"city": "Test City", "country": "US"}
            },
            customer={
                "id": "test_customer",
                "loyalty_tier": "SILVER",
                "historical_velocity_24h": 1,
                "chargebacks_12m": 0
            },
            device={
                "ip": "192.168.1.1",
                "device_id": "test_device",
                "location": {"city": "Test City", "country": "US"}
            },
            geo={"city": "Test City", "country": "US"}
        )

        response = self.agent.process_checkout_enhanced(request)

        for rec in response.recommendations:
            # Check contributions structure
            contributions = rec.explainability["contributions"]
            assert isinstance(contributions, list)
            
            for contrib in contributions:
                assert "feature" in contrib
                assert "value" in contrib
                assert "impact" in contrib
                assert contrib["impact"] in ["positive", "negative"]
                assert isinstance(contrib["value"], (int, float))

            # Check top drivers structure
            top_drivers = rec.explainability["top_drivers"]
            assert isinstance(top_drivers["positive"], list)
            assert isinstance(top_drivers["negative"], list)

            for driver in top_drivers["positive"]:
                assert "feature" in driver
                assert "value" in driver
                assert "magnitude" in driver
                assert driver["value"] > 0
                assert driver["magnitude"] == abs(driver["value"])

            for driver in top_drivers["negative"]:
                assert "feature" in driver
                assert "value" in driver
                assert "magnitude" in driver
                assert driver["value"] < 0
                assert driver["magnitude"] == abs(driver["value"])

    def test_audit_information(self):
        """Test that audit information is properly populated."""
        request = CheckoutRequest(
            merchant_id="test_merchant",
            amount=Decimal("75.00"),
            currency="USD",
            cart={
                "items": [
                    {
                        "item": "Test Item",
                        "unit_price": "75.00",
                        "qty": 1,
                        "mcc": "5411"
                    }
                ],
                "currency": "USD"
            },
            merchant={
                "name": "Test Merchant",
                "mcc": "5411",
                "network_preferences": ["visa"],
                "location": {"city": "Test City", "country": "US"}
            },
            customer={
                "id": "test_customer",
                "loyalty_tier": "PLATINUM",
                "historical_velocity_24h": 1,
                "chargebacks_12m": 0
            },
            device={
                "ip": "192.168.1.1",
                "device_id": "test_device",
                "location": {"city": "Test City", "country": "US"}
            },
            geo={"city": "Test City", "country": "US"}
        )

        response = self.agent.process_checkout_enhanced(request)

        # All recommendations should have the same audit info
        first_audit = response.recommendations[0].audit
        
        for rec in response.recommendations:
            assert rec.audit["request_id"] == first_audit["request_id"]
            assert rec.audit["code_version"] == first_audit["code_version"]
            assert rec.audit["latency_ms"] == first_audit["latency_ms"]
            assert rec.audit["config_versions"] == first_audit["config_versions"]

        # Verify config versions
        config_versions = first_audit["config_versions"]
        assert "config/approval.yaml" in config_versions
        assert "config/preferences.yaml" in config_versions

        # Verify code version is not empty
        assert first_audit["code_version"] != ""

        # Verify request ID is a valid UUID
        import uuid
        try:
            uuid.UUID(first_audit["request_id"])
        except ValueError:
            assert False, "Request ID should be a valid UUID"

    def test_recommendation_ranking(self):
        """Test that recommendations are properly ranked."""
        request = CheckoutRequest(
            merchant_id="test_merchant",
            amount=Decimal("200.00"),
            currency="USD",
            cart={
                "items": [
                    {
                        "item": "Test Item",
                        "unit_price": "200.00",
                        "qty": 1,
                        "mcc": "5411"
                    }
                ],
                "currency": "USD"
            },
            merchant={
                "name": "Test Merchant",
                "mcc": "5411",
                "network_preferences": ["visa"],
                "location": {"city": "Test City", "country": "US"}
            },
            customer={
                "id": "test_customer",
                "loyalty_tier": "GOLD",
                "historical_velocity_24h": 1,
                "chargebacks_12m": 0
            },
            device={
                "ip": "192.168.1.1",
                "device_id": "test_device",
                "location": {"city": "Test City", "country": "US"}
            },
            geo={"city": "Test City", "country": "US"}
        )

        response = self.agent.process_checkout_enhanced(request)

        # Check that ranks are sequential starting from 1
        ranks = [rec.rank for rec in response.recommendations]
        assert ranks == list(range(1, len(ranks) + 1))

        # Check that utility scores are reasonable
        for rec in response.recommendations:
            assert 0.0 <= rec.utility <= 1.0
            assert 0.0 <= rec.p_approval <= 1.0
            assert rec.expected_rewards >= 0.0

    def test_json_serialization(self):
        """Test that enhanced recommendations can be serialized to JSON."""
        request = CheckoutRequest(
            merchant_id="test_merchant",
            amount=Decimal("100.00"),
            currency="USD",
            cart={
                "items": [
                    {
                        "item": "Test Item",
                        "unit_price": "100.00",
                        "qty": 1,
                        "mcc": "5411"
                    }
                ],
                "currency": "USD"
            },
            merchant={
                "name": "Test Merchant",
                "mcc": "5411",
                "network_preferences": ["visa"],
                "location": {"city": "Test City", "country": "US"}
            },
            customer={
                "id": "test_customer",
                "loyalty_tier": "SILVER",
                "historical_velocity_24h": 1,
                "chargebacks_12m": 0
            },
            device={
                "ip": "192.168.1.1",
                "device_id": "test_device",
                "location": {"city": "Test City", "country": "US"}
            },
            geo={"city": "Test City", "country": "US"}
        )

        response = self.agent.process_checkout_enhanced(request)

        # Test JSON serialization
        import json
        json_str = json.dumps(response.model_dump(), default=str)
        assert isinstance(json_str, str)
        assert len(json_str) > 0

        # Test that we can reconstruct the response
        reconstructed = EnhancedCheckoutResponse(
            **json.loads(json_str)
        )
        assert reconstructed.transaction_id == response.transaction_id
        assert len(reconstructed.recommendations) == len(response.recommendations)
