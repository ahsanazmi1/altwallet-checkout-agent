"""Golden test fixtures for AltWallet Intelligence Engine.

This module contains golden test fixtures to ensure deterministic outputs
from the intelligence engine for regression testing.
"""

import json
import os
import pytest
from decimal import Decimal
from pathlib import Path

from src.altwallet_agent.intelligence import IntelligenceEngine
from src.altwallet_agent.models import CheckoutRequest


class TestIntelligenceGolden:
    """Golden test suite for intelligence engine outputs."""

    @pytest.fixture
    def engine(self):
        """Create intelligence engine with deterministic configuration."""
        return IntelligenceEngine({"deterministic_mode": True})

    @pytest.fixture
    def golden_dir(self):
        """Get the golden test fixtures directory."""
        return Path(__file__).parent / "intelligence_outputs"

    def test_amazon_basic_golden(self, engine, golden_dir):
        """Test Amazon basic transaction against golden fixture."""
        request = CheckoutRequest(
            merchant_id="amazon",
            amount=Decimal("150.00"),
            currency="USD",
            user_id="test_user_123",
        )
        
        response = engine.process_checkout_intelligence(request)
        
        # Load expected golden output
        golden_file = golden_dir / "amazon_basic.json"
        if golden_file.exists():
            with open(golden_file, "r") as f:
                expected = json.load(f)
            
            # Compare deterministic parts
            assert response.score == pytest.approx(expected["score"], rel=1e-3)
            assert len(response.recommendations) == expected["recommendations_count"]
            
            # Check recommendation structure
            for i, rec in enumerate(response.recommendations):
                expected_rec = expected["recommendations"][i]
                assert rec["card_id"] == expected_rec["card_id"]
                assert rec["cashback_rate"] == pytest.approx(expected_rec["cashback_rate"], rel=1e-3)
                assert rec["confidence"] == pytest.approx(expected_rec["confidence"], rel=1e-3)
        else:
            # Generate golden fixture if it doesn't exist
            self._create_golden_fixture(response, golden_file)

    def test_hotel_high_value_golden(self, engine, golden_dir):
        """Test hotel high-value transaction against golden fixture."""
        request = CheckoutRequest(
            merchant_id="hotel_marriott",
            amount=Decimal("1200.00"),
            currency="USD",
            user_id="test_user_456",
        )
        
        response = engine.process_checkout_intelligence(request)
        
        golden_file = golden_dir / "hotel_high_value.json"
        if golden_file.exists():
            with open(golden_file, "r") as f:
                expected = json.load(f)
            
            # Compare deterministic parts
            assert response.score == pytest.approx(expected["score"], rel=1e-3)
            assert len(response.recommendations) == expected["recommendations_count"]
            
            # Check that premium cards are recommended
            card_ids = [rec["card_id"] for rec in response.recommendations]
            premium_cards = ["chase_sapphire_reserve", "amex_platinum"]
            has_premium = any(card_id in card_ids for card_id in premium_cards)
            assert has_premium == expected.get("has_premium_cards", True)
        else:
            self._create_golden_fixture(response, golden_file)

    def test_grocery_store_golden(self, engine, golden_dir):
        """Test grocery store transaction against golden fixture."""
        request = CheckoutRequest(
            merchant_id="safeway",
            amount=Decimal("85.50"),
            currency="USD",
            user_id="test_user_789",
        )
        
        response = engine.process_checkout_intelligence(request)
        
        golden_file = golden_dir / "grocery_store.json"
        if golden_file.exists():
            with open(golden_file, "r") as f:
                expected = json.load(f)
            
            assert response.score == pytest.approx(expected["score"], rel=1e-3)
            assert len(response.recommendations) == expected["recommendations_count"]
        else:
            self._create_golden_fixture(response, golden_file)

    def test_foreign_currency_golden(self, engine, golden_dir):
        """Test foreign currency transaction against golden fixture."""
        request = CheckoutRequest(
            merchant_id="foreign_online_store",
            amount=Decimal("200.00"),
            currency="EUR",
            user_id="test_user_international",
        )
        
        response = engine.process_checkout_intelligence(request)
        
        golden_file = golden_dir / "foreign_currency.json"
        if golden_file.exists():
            with open(golden_file, "r") as f:
                expected = json.load(f)
            
            assert response.score == pytest.approx(expected["score"], rel=1e-3)
            assert len(response.recommendations) == expected["recommendations_count"]
            
            # Foreign currency should have higher risk score
            risk_score = engine._assess_risk(request, "test_id")
            assert risk_score >= expected.get("min_risk_score", 0.0)
        else:
            self._create_golden_fixture(response, golden_file)

    def test_risk_scoring_consistency(self, engine):
        """Test that risk scoring is consistent across similar inputs."""
        # Test multiple Amazon transactions
        amazon_requests = [
            CheckoutRequest(
                merchant_id="amazon",
                amount=Decimal(str(amount)),
                currency="USD",
            )
            for amount in [50.00, 100.00, 200.00]
        ]
        
        risk_scores = []
        for req in amazon_requests:
            risk_score = engine._assess_risk(req, "test_id")
            risk_scores.append(risk_score)
        
        # Risk scores should be consistent (Amazon is always low risk)
        assert all(score < 0.5 for score in risk_scores)
        
        # Higher amounts should have slightly higher risk
        assert risk_scores[0] <= risk_scores[1] <= risk_scores[2]

    def test_transaction_scoring_consistency(self, engine):
        """Test that transaction scoring is consistent across similar inputs."""
        # Test multiple transactions with same merchant
        test_requests = [
            CheckoutRequest(
                merchant_id="test_merchant",
                amount=Decimal(str(amount)),
                currency="USD",
            )
            for amount in [100.00, 200.00, 300.00]
        ]
        
        scores = []
        for req in test_requests:
            score = engine._score_transaction(req, "test_id")
            scores.append(score)
        
        # Scores should increase with amount
        assert scores[0] <= scores[1] <= scores[2]
        
        # All scores should be in valid range
        assert all(0.0 <= score <= 1.0 for score in scores)

    def test_recommendation_consistency(self, engine):
        """Test that recommendations are consistent for similar inputs."""
        request = CheckoutRequest(
            merchant_id="amazon",
            amount=Decimal("100.00"),
            currency="USD",
        )
        
        # Get multiple recommendations
        recommendations_list = []
        for i in range(3):
            recs = engine._generate_recommendations(
                request, 0.2, 0.7, f"test_id_{i}"
            )
            recommendations_list.append(recs)
        
        # All recommendations should be identical
        for i in range(1, len(recommendations_list)):
            assert len(recommendations_list[0]) == len(recommendations_list[i])
            for j, rec in enumerate(recommendations_list[0]):
                other_rec = recommendations_list[i][j]
                assert rec["card_id"] == other_rec["card_id"]
                assert rec["cashback_rate"] == other_rec["cashback_rate"]
                assert rec["confidence"] == other_rec["confidence"]

    def _create_golden_fixture(self, response, golden_file: Path):
        """Create golden fixture from response."""
        golden_file.parent.mkdir(parents=True, exist_ok=True)
        
        fixture_data = {
            "score": response.score,
            "recommendations_count": len(response.recommendations),
            "recommendations": [],
            "processing_time_ms": response.metadata.get("processing_time_ms", 0),
        }
        
        # Add recommendation data
        for rec in response.recommendations:
            fixture_data["recommendations"].append({
                "card_id": rec["card_id"],
                "cashback_rate": rec["cashback_rate"],
                "confidence": rec["confidence"],
                "reason": rec["reason"],
            })
        
        # Add special flags
        card_ids = [rec["card_id"] for rec in response.recommendations]
        fixture_data["has_premium_cards"] = any(
            card_id in ["chase_sapphire_reserve", "amex_platinum"]
            for card_id in card_ids
        )
        
        with open(golden_file, "w") as f:
            json.dump(fixture_data, f, indent=2)
        
        pytest.skip(f"Created golden fixture: {golden_file}")


class TestIntelligenceDeterminism:
    """Test suite for ensuring deterministic behavior."""

    def test_deterministic_risk_assessment(self):
        """Test that risk assessment is deterministic."""
        engine = IntelligenceEngine()
        
        request = CheckoutRequest(
            merchant_id="test_merchant",
            amount=Decimal("100.00"),
            currency="USD",
        )
        
        # Same request should produce same risk score
        score1 = engine._assess_risk(request, "test_id")
        score2 = engine._assess_risk(request, "test_id")
        
        assert score1 == score2

    def test_deterministic_transaction_scoring(self):
        """Test that transaction scoring is deterministic."""
        engine = IntelligenceEngine()
        
        request = CheckoutRequest(
            merchant_id="test_merchant",
            amount=Decimal("100.00"),
            currency="USD",
        )
        
        # Same request should produce same transaction score
        score1 = engine._score_transaction(request, "test_id")
        score2 = engine._score_transaction(request, "test_id")
        
        assert score1 == score2

    def test_deterministic_recommendations(self):
        """Test that recommendations are deterministic."""
        engine = IntelligenceEngine()
        
        request = CheckoutRequest(
            merchant_id="amazon",
            amount=Decimal("100.00"),
            currency="USD",
        )
        
        # Same inputs should produce same recommendations
        recs1 = engine._generate_recommendations(request, 0.2, 0.7, "test_id")
        recs2 = engine._generate_recommendations(request, 0.2, 0.7, "test_id")
        
        assert len(recs1) == len(recs2)
        for i, rec1 in enumerate(recs1):
            rec2 = recs2[i]
            assert rec1["card_id"] == rec2["card_id"]
            assert rec1["cashback_rate"] == rec2["cashback_rate"]
            assert rec1["confidence"] == rec2["confidence"]
