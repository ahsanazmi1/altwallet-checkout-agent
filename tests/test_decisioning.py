"""Tests for the decisioning module."""

import pytest

from src.altwallet_agent.decisioning import (
    Decision,
    ActionType,
    PenaltyOrIncentive,
    BusinessRule,
    DecisionReason,
    DecisionContract,
    RoutingHint,
    DecisionEngine,
    make_transaction_decision,
    calculate_decision_thresholds,
    is_decision_approved,
    is_decision_review_required,
    is_decision_declined,
)
from src.altwallet_agent.models import (
    Context, Cart, CartItem, Merchant, Customer, Device, Geo, LoyaltyTier
)
from src.altwallet_agent.scoring import ScoreResult


class TestDecisionEnums:
    """Test decision and action type enums."""
    
    def test_decision_values(self):
        """Test decision enum values."""
        assert Decision.APPROVE == "APPROVE"
        assert Decision.REVIEW == "REVIEW"
        assert Decision.DECLINE == "DECLINE"
    
    def test_action_type_values(self):
        """Test action type enum values."""
        assert ActionType.KYC_REQUIRED == "KYC_REQUIRED"
        assert ActionType.LOYALTY_BOOST == "LOYALTY_BOOST"
        assert ActionType.NETWORK_ROUTING == "NETWORK_ROUTING"
    
    def test_penalty_or_incentive_values(self):
        """Test penalty or incentive enum values."""
        assert PenaltyOrIncentive.SURCHARGE == "surcharge"
        assert PenaltyOrIncentive.SUPPRESSION == "suppression"
        assert PenaltyOrIncentive.NONE == "none"


class TestRoutingHint:
    """Test RoutingHint model."""
    
    def test_routing_hint_creation(self):
        """Test creating a routing hint."""
        hint = RoutingHint(
            preferred_network="visa",
            preferred_acquirer="acq_123",
            penalty_or_incentive=PenaltyOrIncentive.SUPPRESSION,
            approval_odds=0.85,
            network_preferences=["visa", "mc"],
            mcc_based_hint="prefer_visa",
            confidence=0.9
        )
        
        assert hint.preferred_network == "visa"
        assert hint.preferred_acquirer == "acq_123"
        assert hint.penalty_or_incentive == PenaltyOrIncentive.SUPPRESSION
        assert hint.approval_odds == 0.85
        assert hint.network_preferences == ["visa", "mc"]
        assert hint.mcc_based_hint == "prefer_visa"
        assert hint.confidence == 0.9
        assert hint.has_preference is True
        assert hint.has_penalty_or_incentive is True
    
    def test_routing_hint_defaults(self):
        """Test routing hint with default values."""
        hint = RoutingHint()
        
        assert hint.preferred_network == "any"
        assert hint.preferred_acquirer is None
        assert hint.penalty_or_incentive == PenaltyOrIncentive.NONE
        assert hint.approval_odds is None
        assert hint.network_preferences == []
        assert hint.mcc_based_hint is None
        assert hint.confidence == 0.8
        assert hint.has_preference is False
        assert hint.has_penalty_or_incentive is False
    
    def test_routing_hint_computed_fields(self):
        """Test routing hint computed fields."""
        # Test with preference
        hint_with_pref = RoutingHint(preferred_network="mc")
        assert hint_with_pref.has_preference is True
        
        # Test without preference
        hint_no_pref = RoutingHint(preferred_network="any")
        assert hint_no_pref.has_preference is False
        
        # Test with penalty
        hint_with_penalty = RoutingHint(
            penalty_or_incentive=PenaltyOrIncentive.SURCHARGE
        )
        assert hint_with_penalty.has_penalty_or_incentive is True
        
        # Test without penalty
        hint_no_penalty = RoutingHint(
            penalty_or_incentive=PenaltyOrIncentive.NONE
        )
        assert hint_no_penalty.has_penalty_or_incentive is False


class TestBusinessRule:
    """Test BusinessRule model."""
    
    def test_business_rule_creation(self):
        """Test creating a business rule."""
        rule = BusinessRule(
            rule_id="TEST_001",
            action_type=ActionType.KYC_REQUIRED,
            description="Test rule",
            parameters={"test": "value"},
            impact_score=10.0
        )
        
        assert rule.rule_id == "TEST_001"
        assert rule.action_type == ActionType.KYC_REQUIRED
        assert rule.description == "Test rule"
        assert rule.parameters == {"test": "value"}
        assert rule.impact_score == 10.0


class TestDecisionReason:
    """Test DecisionReason model."""
    
    def test_decision_reason_creation(self):
        """Test creating a decision reason."""
        reason = DecisionReason(
            feature_name="test_feature",
            value=True,
            threshold=False,
            weight=0.5,
            description="Test reason"
        )
        
        assert reason.feature_name == "test_feature"
        assert reason.value is True
        assert reason.threshold is False
        assert reason.weight == 0.5
        assert reason.description == "Test reason"


class TestDecisionContract:
    """Test DecisionContract model."""
    
    def test_decision_contract_creation(self):
        """Test creating a decision contract."""
        routing_hint = RoutingHint()
        contract = DecisionContract(
            decision=Decision.APPROVE,
            actions=[],
            reasons=[],
            routing_hint=routing_hint,
            transaction_id="test_123",
            confidence=0.9
        )
        
        assert contract.decision == Decision.APPROVE
        assert contract.transaction_id == "test_123"
        assert contract.confidence == 0.9
        assert contract.is_approved is True
        assert contract.requires_review is False
        assert contract.is_declined is False
        assert contract.routing_hint == routing_hint
    
    def test_decision_contract_json_serialization(self):
        """Test JSON serialization of decision contract."""
        routing_hint = RoutingHint()
        contract = DecisionContract(
            decision=Decision.REVIEW,
            actions=[],
            reasons=[],
            routing_hint=routing_hint,
            transaction_id="test_456"
        )
        
        json_str = contract.to_json()
        assert isinstance(json_str, str)
        assert "REVIEW" in json_str
        assert "test_456" in json_str
    
    def test_decision_contract_dict_conversion(self):
        """Test dictionary conversion of decision contract."""
        routing_hint = RoutingHint()
        contract = DecisionContract(
            decision=Decision.DECLINE,
            actions=[],
            reasons=[],
            routing_hint=routing_hint,
            transaction_id="test_789"
        )
        
        contract_dict = contract.to_dict()
        assert isinstance(contract_dict, dict)
        assert contract_dict["decision"] == "DECLINE"
        assert contract_dict["transaction_id"] == "test_789"
        assert "routing_hint" in contract_dict


class TestDecisionEngine:
    """Test DecisionEngine class."""
    
    def test_decision_engine_initialization(self):
        """Test decision engine initialization."""
        engine = DecisionEngine()
        
        assert engine.approve_threshold == 70
        assert engine.review_threshold == 40
        assert isinstance(engine.business_rules, dict)
    
    def test_decision_determination(self):
        """Test decision determination logic."""
        engine = DecisionEngine()
        
        # Test approve threshold
        decision = engine._determine_decision(80)
        assert decision == Decision.APPROVE
        
        # Test review threshold
        decision = engine._determine_decision(50)
        assert decision == Decision.REVIEW
        
        # Test decline threshold
        decision = engine._determine_decision(30)
        assert decision == Decision.DECLINE
    
    def test_routing_hint_calculation(self):
        """Test routing hint calculation."""
        engine = DecisionEngine()
        
        # Create test context
        context = self._create_test_context()
        
        # Create mock score result
        from src.altwallet_agent.scoring import ScoreResult
        score_result = ScoreResult(
            risk_score=20,
            loyalty_boost=10,
            final_score=90,
            routing_hint="prefer_visa",
            signals={}
        )
        
        # Calculate routing hint
        routing_hint = engine._calculate_routing_hint(context, score_result)
        
        assert isinstance(routing_hint, RoutingHint)
        assert routing_hint.preferred_network == "prefer_visa"
        assert routing_hint.approval_odds is not None
        assert routing_hint.confidence > 0.0
    
    def test_penalty_or_incentive_calculation(self):
        """Test penalty or incentive calculation."""
        engine = DecisionEngine()
        
        # Create test context
        context = self._create_test_context()
        
        # Test high-risk transaction (should get surcharge)
        high_risk_score = ScoreResult(
            risk_score=80, loyalty_boost=0, final_score=20,
            routing_hint="any", signals={}
        )
        penalty = engine._calculate_penalty_or_incentive(
            context, high_risk_score
        )
        assert penalty == PenaltyOrIncentive.SURCHARGE
        
        # Test premium customer (should get suppression)
        premium_context = self._create_test_context(
            loyalty_tier=LoyaltyTier.GOLD
        )
        normal_score = ScoreResult(
            risk_score=10, loyalty_boost=10, final_score=100,
            routing_hint="any", signals={}
        )
        penalty = engine._calculate_penalty_or_incentive(
            premium_context, normal_score
        )
        assert penalty == PenaltyOrIncentive.SUPPRESSION
        
        # Test normal transaction (should get none)
        normal_context = self._create_test_context()
        normal_score = ScoreResult(
            risk_score=10, loyalty_boost=5, final_score=95,
            routing_hint="any", signals={}
        )
        penalty = engine._calculate_penalty_or_incentive(
            normal_context, normal_score
        )
        assert penalty == PenaltyOrIncentive.NONE
    
    def test_approval_odds_calculation(self):
        """Test approval odds calculation."""
        engine = DecisionEngine()
        
        # Test various score ranges
        test_cases = [
            (10, 0.1),    # Very low score
            (30, 0.3),    # Low score
            (55, 0.55),   # Medium score
            (85, 0.8245), # High score (actual calculation)
            (110, 0.975)  # Very high score
        ]
        
        for score, expected_odds in test_cases:
            score_result = ScoreResult(
                risk_score=100-score, loyalty_boost=0, final_score=score,
                routing_hint="any", signals={}
            )
            odds = engine._calculate_approval_odds(score_result)
            assert abs(odds - expected_odds) < 0.01
    
    def _create_test_context(self, loyalty_tier=LoyaltyTier.SILVER):
        """Create a test context for testing."""
        cart_items = [
            CartItem(
                item="Test Item",
                unit_price="100.00",
                qty=1,
                mcc="5411"
            )
        ]
        
        cart = Cart(items=cart_items, currency="USD")
        
        merchant = Merchant(
            name="Test Merchant",
            mcc="5411",
            network_preferences=["visa"]
        )
        
        customer = Customer(
            id="test_customer",
            loyalty_tier=loyalty_tier,
            historical_velocity_24h=2,
            chargebacks_12m=0
        )
        
        device = Device(
            ip="192.168.1.1",
            device_id="test_device",
            location={"city": "Test City", "country": "Test Country"}
        )
        
        geo = Geo(
            city="Test City",
            country="Test Country"
        )
        
        return Context(
            cart=cart,
            merchant=merchant,
            customer=customer,
            device=device,
            geo=geo
        )


class TestDecisioningFunctions:
    """Test decisioning utility functions."""
    
    def test_calculate_decision_thresholds(self):
        """Test decision threshold calculation."""
        thresholds = calculate_decision_thresholds()
        
        assert thresholds["approve"] == 70
        assert thresholds["review"] == 40
        assert thresholds["decline"] == 0
    
    def test_decision_checks(self):
        """Test decision checking functions."""
        assert is_decision_approved(Decision.APPROVE) is True
        assert is_decision_approved(Decision.REVIEW) is False
        
        assert is_decision_review_required(Decision.REVIEW) is True
        assert is_decision_review_required(Decision.APPROVE) is False
        
        assert is_decision_declined(Decision.DECLINE) is True
        assert is_decision_declined(Decision.APPROVE) is False


class TestIntegration:
    """Test integration with real context data."""
    
    def test_full_decision_flow(self):
        """Test the complete decision flow."""
        context = self._create_test_context()
        
        # Test with decision engine
        engine = DecisionEngine()
        decision = engine.make_decision(context, "test_txn_001")
        
        assert isinstance(decision, DecisionContract)
        assert decision.transaction_id == "test_txn_001"
        assert decision.score_result is not None
        assert decision.confidence > 0.0
        assert decision.routing_hint is not None
        
        # Test convenience function
        quick_decision = make_transaction_decision(context, "test_txn_002")
        
        assert isinstance(quick_decision, DecisionContract)
        assert quick_decision.transaction_id == "test_txn_002"
        assert quick_decision.decision == decision.decision  # Same context, same decision
        assert quick_decision.routing_hint is not None
    
    def _create_test_context(self):
        """Create a test context for integration testing."""
        cart_items = [
            CartItem(
                item="Test Item",
                unit_price="100.00",
                qty=1,
                mcc="5411"
            )
        ]
        
        cart = Cart(items=cart_items, currency="USD")
        
        merchant = Merchant(
            name="Test Merchant",
            mcc="5411",
            network_preferences=["visa"]
        )
        
        customer = Customer(
            id="test_customer",
            loyalty_tier=LoyaltyTier.SILVER,
            historical_velocity_24h=2,
            chargebacks_12m=0
        )
        
        device = Device(
            ip="192.168.1.1",
            device_id="test_device",
            location={"city": "Test City", "country": "Test Country"}
        )
        
        geo = Geo(
            city="Test City",
            country="Test Country"
        )
        
        return Context(
            cart=cart,
            merchant=merchant,
            customer=customer,
            device=device,
            geo=geo
        )


if __name__ == "__main__":
    pytest.main([__file__])
