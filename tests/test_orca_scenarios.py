"""
Tests for Orca-specific scenarios and features.

This module tests the new Orca decision engine features including:
- Decision types (APPROVE/REVIEW/DECLINE)
- Actions (discount, KYC, risk_review, surcharge_suppression)
- Routing hints (network preferences, interchange optimization)
- Orca features (loyalty boosts, risk assessment, velocity analysis)
"""

import json
import pytest
from pathlib import Path

from altwallet_agent.core import CheckoutAgent
from altwallet_agent.models import CheckoutRequest, CheckoutResponse


class TestOrcaScenarios:
    """Test Orca-specific scenarios and decision engine features."""
    
    @pytest.fixture
    def agent(self):
        """Create a CheckoutAgent instance for testing."""
        return CheckoutAgent()
    
    @pytest.fixture
    def orca_fixtures_dir(self):
        """Get the path to Orca test fixtures."""
        return Path(__file__).parent / "golden" / "fixtures"
    
    @pytest.fixture
    def orca_snapshots_dir(self):
        """Get the path to Orca test snapshots."""
        return Path(__file__).parent / "golden" / "snapshots"
    
    def test_orca_online_grocery_scenario(self, agent, orca_fixtures_dir, orca_snapshots_dir):
        """Test Orca online grocery scenario with loyalty boost."""
        # Load test fixture
        fixture_path = orca_fixtures_dir / "11_orca_online_grocery.json"
        with open(fixture_path) as f:
            fixture_data = json.load(f)
        
        # Load expected snapshot
        snapshot_path = orca_snapshots_dir / "11_orca_online_grocery.json"
        with open(snapshot_path) as f:
            expected_response = json.load(f)
        
        # Create request
        request = CheckoutRequest(**fixture_data)
        
        # Process request
        response = agent.process_checkout(request)
        
        # Validate Orca-specific fields
        assert response.decision == "APPROVE"
        assert response.score >= 0.8  # High score for grocery with loyalty
        assert len(response.actions) > 0
        assert response.routing_hints is not None
        assert "orca_features" in response.metadata
        
        # Validate actions
        action_types = [action.type for action in response.actions]
        assert "discount" in action_types
        assert "loyalty_boost" in action_types
        
        # Validate routing hints
        assert response.routing_hints.preferred_network in ["visa", "mc", "amex"]
        assert response.routing_hints.interchange_optimization is True
        
        # Validate Orca features
        orca_features = response.metadata.get("orca_features", [])
        assert "interchange_optimization" in orca_features
        assert "loyalty_boost" in orca_features
        assert "risk_assessment" in orca_features
    
    def test_orca_in_person_retail_scenario(self, agent, orca_fixtures_dir, orca_snapshots_dir):
        """Test Orca in-person retail scenario with platinum tier benefits."""
        # Load test fixture
        fixture_path = orca_fixtures_dir / "12_orca_in_person_retail.json"
        with open(fixture_path) as f:
            fixture_data = json.load(f)
        
        # Create request
        request = CheckoutRequest(**fixture_data)
        
        # Process request
        response = agent.process_checkout(request)
        
        # Validate Orca-specific fields
        assert response.decision == "APPROVE"
        assert response.score >= 0.9  # Very high score for platinum tier
        assert len(response.actions) > 0
        assert response.routing_hints is not None
        
        # Validate actions for platinum tier
        action_types = [action.type for action in response.actions]
        assert "loyalty_boost" in action_types
        assert "discount" in action_types
        
        # Validate routing hints for electronics
        assert response.routing_hints.preferred_network in ["visa", "mc", "amex"]
        assert response.routing_hints.interchange_optimization is True
        
        # Validate Orca features
        orca_features = response.metadata.get("orca_features", [])
        assert "interchange_optimization" in orca_features
        assert "loyalty_boost" in orca_features
        assert "platinum_tier_benefits" in orca_features
    
    def test_orca_high_risk_cross_border_scenario(self, agent, orca_fixtures_dir, orca_snapshots_dir):
        """Test Orca high-risk cross-border scenario requiring review."""
        # Load test fixture
        fixture_path = orca_fixtures_dir / "13_orca_high_risk_cross_border.json"
        with open(fixture_path) as f:
            fixture_data = json.load(f)
        
        # Create request
        request = CheckoutRequest(**fixture_data)
        
        # Process request
        response = agent.process_checkout(request)
        
        # Validate Orca-specific fields
        assert response.decision == "REVIEW"  # Should require review
        assert response.score < 0.6  # Lower score due to risk factors
        assert len(response.actions) > 0
        assert response.routing_hints is not None
        
        # Validate actions for high-risk scenario
        action_types = [action.type for action in response.actions]
        assert "kyc_required" in action_types
        assert "risk_review" in action_types
        assert "surcharge_suppression" in action_types
        
        # Validate routing hints for risk mitigation
        assert response.routing_hints.surcharge_suppression is True
        assert response.routing_hints.interchange_optimization is False
        
        # Validate Orca features
        orca_features = response.metadata.get("orca_features", [])
        assert "risk_assessment" in orca_features
        assert "cross_border_detection" in orca_features
        assert "velocity_analysis" in orca_features
        assert "chargeback_monitoring" in orca_features
    
    def test_orca_surcharge_suppression_scenario(self, agent, orca_fixtures_dir, orca_snapshots_dir):
        """Test Orca surcharge suppression scenario for gas stations."""
        # Load test fixture
        fixture_path = orca_fixtures_dir / "14_orca_surcharge_suppression.json"
        with open(fixture_path) as f:
            fixture_data = json.load(f)
        
        # Create request
        request = CheckoutRequest(**fixture_data)
        
        # Process request
        response = agent.process_checkout(request)
        
        # Validate Orca-specific fields
        assert response.decision == "APPROVE"
        assert response.score >= 0.7  # Good score with surcharge suppression
        assert len(response.actions) > 0
        assert response.routing_hints is not None
        
        # Validate actions for surcharge suppression
        action_types = [action.type for action in response.actions]
        assert "surcharge_suppression" in action_types
        assert "discount" in action_types
        
        # Validate routing hints
        assert response.routing_hints.surcharge_suppression is True
        assert response.routing_hints.interchange_optimization is True
        
        # Validate Orca features
        orca_features = response.metadata.get("orca_features", [])
        assert "interchange_optimization" in orca_features
        assert "surcharge_suppression" in orca_features
        assert "gas_category_boost" in orca_features
    
    def test_orca_loyalty_boost_scenario(self, agent, orca_fixtures_dir, orca_snapshots_dir):
        """Test Orca loyalty boost scenario for diamond tier customers."""
        # Load test fixture
        fixture_path = orca_fixtures_dir / "15_orca_loyalty_boost.json"
        with open(fixture_path) as f:
            fixture_data = json.load(f)
        
        # Create request
        request = CheckoutRequest(**fixture_data)
        
        # Process request
        response = agent.process_checkout(request)
        
        # Validate Orca-specific fields
        assert response.decision == "APPROVE"
        assert response.score >= 0.9  # Very high score for diamond tier
        assert len(response.actions) > 0
        assert response.routing_hints is not None
        
        # Validate actions for diamond tier
        action_types = [action.type for action in response.actions]
        assert "loyalty_boost" in action_types
        assert "discount" in action_types
        assert "premium_service" in action_types
        
        # Validate routing hints
        assert response.routing_hints.preferred_network in ["amex", "visa", "mc"]
        assert response.routing_hints.interchange_optimization is True
        
        # Validate Orca features
        orca_features = response.metadata.get("orca_features", [])
        assert "interchange_optimization" in orca_features
        assert "loyalty_boost" in orca_features
        assert "diamond_tier_benefits" in orca_features
        assert "premium_service_activation" in orca_features
    
    def test_orca_decision_types(self, agent):
        """Test that Orca decision engine returns valid decision types."""
        # Test data for different decision scenarios
        test_scenarios = [
            {
                "name": "low_risk_approve",
                "data": {
                    "cart": {"items": [{"item": "Test", "unit_price": "10.00", "qty": 1, "mcc": "5411", "merchant_category": "Grocery"}], "currency": "USD"},
                    "merchant": {"name": "Test Store", "mcc": "5411", "network_preferences": ["visa"], "location": {"city": "Test", "country": "US"}},
                    "customer": {"id": "test", "loyalty_tier": "GOLD", "historical_velocity_24h": 1, "chargebacks_12m": 0},
                    "device": {"ip": "192.168.1.1", "device_id": "test", "ip_distance_km": 0.1, "location": {"city": "Test", "country": "US"}},
                    "geo": {"city": "Test", "region": "CA", "country": "US", "lat": 37.7749, "lon": -122.4194}
                },
                "expected_decision": "APPROVE"
            },
            {
                "name": "high_risk_review",
                "data": {
                    "cart": {"items": [{"item": "Test", "unit_price": "5000.00", "qty": 1, "mcc": "5094", "merchant_category": "Jewelry"}], "currency": "USD"},
                    "merchant": {"name": "Test Store", "mcc": "5094", "network_preferences": ["visa"], "location": {"city": "Test", "country": "CA"}},
                    "customer": {"id": "test", "loyalty_tier": "NONE", "historical_velocity_24h": 20, "chargebacks_12m": 2},
                    "device": {"ip": "203.0.113.1", "device_id": "test", "ip_distance_km": 1000.0, "location": {"city": "Test", "country": "US"}},
                    "geo": {"city": "Test", "region": "ON", "country": "CA", "lat": 43.6532, "lon": -79.3832}
                },
                "expected_decision": "REVIEW"
            }
        ]
        
        for scenario in test_scenarios:
            request = CheckoutRequest(**scenario["data"])
            response = agent.process_checkout(request)
            
            # Validate decision type
            assert response.decision in ["APPROVE", "REVIEW", "DECLINE"]
            
            # Validate Orca-specific fields are present
            assert response.actions is not None
            assert response.routing_hints is not None
            assert "orca_features" in response.metadata
    
    def test_orca_action_types(self, agent):
        """Test that Orca returns valid action types."""
        # Create a test request
        test_data = {
            "cart": {"items": [{"item": "Test", "unit_price": "100.00", "qty": 1, "mcc": "5411", "merchant_category": "Grocery"}], "currency": "USD"},
            "merchant": {"name": "Test Store", "mcc": "5411", "network_preferences": ["visa"], "location": {"city": "Test", "country": "US"}},
            "customer": {"id": "test", "loyalty_tier": "GOLD", "historical_velocity_24h": 1, "chargebacks_12m": 0},
            "device": {"ip": "192.168.1.1", "device_id": "test", "ip_distance_km": 0.1, "location": {"city": "Test", "country": "US"}},
            "geo": {"city": "Test", "region": "CA", "country": "US", "lat": 37.7749, "lon": -122.4194}
        }
        
        request = CheckoutRequest(**test_data)
        response = agent.process_checkout(request)
        
        # Validate action types
        valid_action_types = ["discount", "loyalty_boost", "kyc_required", "risk_review", "surcharge_suppression", "premium_service"]
        
        for action in response.actions:
            assert action.type in valid_action_types
            assert action.value is not None
            assert action.description is not None
    
    def test_orca_routing_hints(self, agent):
        """Test that Orca returns valid routing hints."""
        # Create a test request
        test_data = {
            "cart": {"items": [{"item": "Test", "unit_price": "100.00", "qty": 1, "mcc": "5411", "merchant_category": "Grocery"}], "currency": "USD"},
            "merchant": {"name": "Test Store", "mcc": "5411", "network_preferences": ["visa", "mc"], "location": {"city": "Test", "country": "US"}},
            "customer": {"id": "test", "loyalty_tier": "GOLD", "historical_velocity_24h": 1, "chargebacks_12m": 0},
            "device": {"ip": "192.168.1.1", "device_id": "test", "ip_distance_km": 0.1, "location": {"city": "Test", "country": "US"}},
            "geo": {"city": "Test", "region": "CA", "country": "US", "lat": 37.7749, "lon": -122.4194}
        }
        
        request = CheckoutRequest(**test_data)
        response = agent.process_checkout(request)
        
        # Validate routing hints
        routing_hints = response.routing_hints
        
        valid_networks = ["visa", "mc", "mastercard", "amex", "discover"]
        assert routing_hints.preferred_network in valid_networks
        
        for network in routing_hints.fallback_networks:
            assert network in valid_networks
        
        assert isinstance(routing_hints.interchange_optimization, bool)
        assert isinstance(routing_hints.surcharge_suppression, bool)
    
    def test_orca_features_metadata(self, agent):
        """Test that Orca features are properly included in metadata."""
        # Create a test request
        test_data = {
            "cart": {"items": [{"item": "Test", "unit_price": "100.00", "qty": 1, "mcc": "5411", "merchant_category": "Grocery"}], "currency": "USD"},
            "merchant": {"name": "Test Store", "mcc": "5411", "network_preferences": ["visa"], "location": {"city": "Test", "country": "US"}},
            "customer": {"id": "test", "loyalty_tier": "GOLD", "historical_velocity_24h": 1, "chargebacks_12m": 0},
            "device": {"ip": "192.168.1.1", "device_id": "test", "ip_distance_km": 0.1, "location": {"city": "Test", "country": "US"}},
            "geo": {"city": "Test", "region": "CA", "country": "US", "lat": 37.7749, "lon": -122.4194}
        }
        
        request = CheckoutRequest(**test_data)
        response = agent.process_checkout(request)
        
        # Validate Orca features metadata
        assert "orca_features" in response.metadata
        orca_features = response.metadata["orca_features"]
        
        assert isinstance(orca_features, list)
        assert len(orca_features) > 0
        
        # Validate that common Orca features are present
        common_features = ["risk_assessment", "interchange_optimization"]
        for feature in common_features:
            assert feature in orca_features
        
        # Validate metadata structure
        assert "processing_time_ms" in response.metadata
        assert "intelligence_version" in response.metadata
        assert "algorithm_used" in response.metadata
        assert response.metadata["algorithm_used"] == "orca_intelligence_engine"


if __name__ == '__main__':
    pytest.main([__file__])
