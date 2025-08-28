"""Unit tests for AltWallet Intelligence Engine.

This module contains comprehensive tests for the intelligence engine
including risk assessment, transaction scoring, and recommendations.
"""

from decimal import Decimal

import pytest

from altwallet_agent.intelligence import IntelligenceEngine
from altwallet_agent.models import CheckoutRequest


class TestIntelligenceEngine:
    """Test suite for the IntelligenceEngine class."""

    @pytest.fixture
    def engine(self):
        """Create a fresh intelligence engine for each test."""
        return IntelligenceEngine()

    @pytest.fixture
    def basic_request(self):
        """Create a basic checkout request for testing."""
        return CheckoutRequest(
            merchant_id="amazon",
            amount=Decimal("150.00"),
            currency="USD",
            user_id="test_user_123",
        )

    @pytest.fixture
    def high_value_request(self):
        """Create a high-value checkout request for testing."""
        return CheckoutRequest(
            merchant_id="hotel_marriott",
            amount=Decimal("1200.00"),
            currency="USD",
            user_id="test_user_456",
        )

    def test_engine_initialization(self, engine):
        """Test that the intelligence engine initializes correctly."""
        assert engine is not None
        assert engine.config == {}
        assert engine.processing_time_ms == 0.0
        assert engine.logger is not None

    def test_engine_initialization_with_config(self):
        """Test engine initialization with custom configuration."""
        config = {"risk_threshold": 0.7, "max_recommendations": 3}
        engine = IntelligenceEngine(config)

        assert engine.config == config
        assert engine.logger is not None

    def test_process_checkout_intelligence_basic(self, engine, basic_request):
        """Test basic checkout processing with intelligence."""
        response = engine.process_checkout_intelligence(basic_request)

        # Verify response structure
        assert response.transaction_id is not None
        assert len(response.recommendations) > 0
        assert 0.0 <= response.score <= 1.0
        assert response.status == "completed"
        assert "intelligence_version" in response.metadata

        # Verify processing time was recorded
        assert engine.processing_time_ms >= 0

        # Verify request_id correlation
        assert response.metadata["request_id"] == response.transaction_id

    def test_process_checkout_intelligence_high_value(self, engine, high_value_request):
        """Test high-value transaction processing."""
        response = engine.process_checkout_intelligence(high_value_request)

        # High-value transactions should get different recommendations
        assert response.transaction_id is not None
        assert len(response.recommendations) > 0
        assert response.status == "completed"

        # High-value transactions should have premium card options
        card_names = [rec["name"] for rec in response.recommendations]
        premium_cards = [
            "Chase Sapphire Reserve",
            "American Express Platinum",
        ]

        # High-value transactions should have appropriate recommendations
        has_premium = any(card in card_names for card in premium_cards)
        # Either premium cards or Chase Sapphire Preferred should be recommended
        assert has_premium or response.recommendations[0]["card_id"] in [
            "chase_sapphire_preferred",
            "chase_sapphire_reserve",
        ]

    def test_risk_assessment_amazon_transaction(self, engine, basic_request):
        """Test risk assessment for Amazon transactions."""
        risk_score = engine._assess_risk(basic_request, "test_request_id")

        # Amazon transactions should have lower risk
        assert 0.0 <= risk_score <= 1.0
        assert risk_score < 0.5  # Amazon should be low risk

    def test_risk_assessment_high_value_transaction(self, engine, high_value_request):
        """Test risk assessment for high-value transactions."""
        risk_score = engine._assess_risk(high_value_request, "test_request_id")

        # High-value transactions should have higher risk
        assert 0.0 <= risk_score <= 1.0
        assert risk_score > 0.3  # High-value should be higher risk

    def test_transaction_scoring_deterministic(self, engine, basic_request):
        """Test that transaction scoring is deterministic."""
        # Same request should produce same score
        score1 = engine._score_transaction(basic_request, "test_request_id")
        score2 = engine._score_transaction(basic_request, "test_request_id")

        assert score1 == score2
        assert 0.0 <= score1 <= 1.0

    def test_transaction_scoring_amount_bonus(self, engine):
        """Test that higher amounts get scoring bonuses."""
        low_amount_request = CheckoutRequest(
            merchant_id="test_merchant",
            amount=Decimal("50.00"),
            currency="USD",
        )

        high_amount_request = CheckoutRequest(
            merchant_id="test_merchant",
            amount=Decimal("500.00"),
            currency="USD",
        )

        low_score = engine._score_transaction(low_amount_request, "test_id")
        high_score = engine._score_transaction(high_amount_request, "test_id")

        # Higher amounts should get higher scores
        assert high_score > low_score

    def test_recommendations_amazon_specific(self, engine, basic_request):
        """Test Amazon-specific card recommendations."""
        risk_score = 0.2  # Low risk for Amazon
        transaction_score = 0.7  # Good transaction score

        recommendations = engine._generate_recommendations(
            basic_request, risk_score, transaction_score, "test_id"
        )

        # Should include Amazon-specific cards
        card_ids = [rec["card_id"] for rec in recommendations]
        assert "amazon_rewards_visa" in card_ids

        # Verify recommendation structure
        for rec in recommendations:
            assert "card_id" in rec
            assert "name" in rec
            assert "cashback_rate" in rec
            assert "reason" in rec
            assert "confidence" in rec

    def test_recommendations_high_risk_high_value(self, engine, high_value_request):
        """Test recommendations for high-risk, high-value transactions."""
        risk_score = 0.8  # High risk
        transaction_score = 0.9  # High transaction score

        recommendations = engine._generate_recommendations(
            high_value_request, risk_score, transaction_score, "test_id"
        )

        # High-risk, high-value should get premium cards
        card_ids = [rec["card_id"] for rec in recommendations]
        premium_card_ids = ["chase_sapphire_reserve", "amex_platinum"]

        # Should include at least one premium card
        has_premium = any(card_id in card_ids for card_id in premium_card_ids)
        assert has_premium

    def test_final_score_calculation(self, engine):
        """Test final score calculation logic."""
        risk_score = 0.3
        transaction_score = 0.8
        recommendations = [{"card_id": "test_card"}]

        final_score = engine._calculate_final_score(
            risk_score, transaction_score, recommendations
        )

        # Score should be weighted combination
        expected_score = transaction_score * 0.6 - risk_score * 0.4
        assert abs(final_score - expected_score) < 0.01
        assert 0.0 <= final_score <= 1.0

    def test_response_preparation(self, engine, basic_request):
        """Test response preparation with metadata."""
        request_id = "test_transaction_123"
        recommendations = [
            {
                "card_id": "test_card",
                "name": "Test Card",
                "cashback_rate": 0.02,
                "reason": "Test reason",
                "confidence": 0.8,
            }
        ]
        final_score = 0.75

        response = engine._prepare_response(
            request_id, recommendations, final_score, basic_request
        )

        # Verify response structure
        assert response.transaction_id == request_id
        assert response.recommendations == recommendations
        assert response.score == final_score
        assert response.status == "completed"

        # Verify metadata
        metadata = response.metadata
        assert "processing_time_ms" in metadata
        assert "request_id" in metadata
        assert "intelligence_version" in metadata
        assert "algorithm_used" in metadata

    def test_processing_stats(self, engine):
        """Test processing statistics retrieval."""
        stats = engine.get_processing_stats()

        assert "last_processing_time_ms" in stats
        assert "engine_version" in stats
        assert "config_keys" in stats

        # Initially should be 0 processing time
        assert stats["last_processing_time_ms"] == 0.0

    def test_error_handling_invalid_request(self, engine):
        """Test error handling for invalid requests."""
        with pytest.raises((RuntimeError, AttributeError)):
            # Pass None instead of valid request
            engine.process_checkout_intelligence(None)  # type: ignore

    def test_deterministic_outputs(self, engine, basic_request):
        """Test that same inputs produce same outputs."""
        # Process same request multiple times
        response1 = engine.process_checkout_intelligence(basic_request)
        response2 = engine.process_checkout_intelligence(basic_request)

        # Scores should be deterministic (but transaction IDs will differ)
        assert response1.score == response2.score
        assert len(response1.recommendations) == len(response2.recommendations)

        # Recommendation content should be the same
        for i, rec1 in enumerate(response1.recommendations):
            rec2 = response2.recommendations[i]
            assert rec1["card_id"] == rec2["card_id"]
            assert rec1["cashback_rate"] == rec2["cashback_rate"]
            assert rec1["confidence"] == rec2["confidence"]

    def test_foreign_currency_handling(self, engine):
        """Test handling of foreign currency transactions."""
        foreign_request = CheckoutRequest(
            merchant_id="foreign_merchant",
            amount=Decimal("100.00"),
            currency="EUR",
            user_id="test_user",
        )

        response = engine.process_checkout_intelligence(foreign_request)

        # Should handle foreign currency
        assert response.status == "completed"
        assert 0.0 <= response.score <= 1.0

        # Foreign currency should affect risk assessment
        risk_score = engine._assess_risk(foreign_request, "test_id")
        assert risk_score > 0.0

    def test_processing_time_tracking(self, engine, basic_request):
        """Test that processing time is accurately tracked."""
        # Process request
        engine.process_checkout_intelligence(basic_request)

        # Should have recorded processing time
        assert engine.processing_time_ms >= 0.0

        # Should be reasonable (less than 1 second)
        assert engine.processing_time_ms < 1000.0
