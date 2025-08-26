"""Golden tests for checkout responses."""

import json
from pathlib import Path
from decimal import Decimal

import pytest

from altwallet_agent import CheckoutAgent
from altwallet_agent.models import CheckoutRequest


class TestCheckoutGoldenTests:
    """Golden tests for checkout processing."""

    @pytest.fixture
    def agent(self):
        """Create a test agent instance."""
        return CheckoutAgent()

    @pytest.fixture
    def golden_data_dir(self):
        """Get the golden data directory."""
        return Path(__file__).parent / "data"

    def test_small_transaction_response(self, agent, golden_data_dir):
        """Test response for small transaction amount."""
        request = CheckoutRequest(
            merchant_id="small_merchant", amount=Decimal("10.00"), currency="USD"
        )

        response = agent.process_checkout(request)

        # Basic structure validation
        assert response.transaction_id is not None
        assert response.score >= 0 and response.score <= 1
        assert response.status == "completed"
        assert isinstance(response.recommendations, list)

        # Save golden data if directory exists
        if golden_data_dir.exists():
            golden_file = golden_data_dir / "small_transaction_response.json"
            golden_data = {
                "request": {
                    "merchant_id": request.merchant_id,
                    "amount": str(request.amount),
                    "currency": request.currency,
                },
                "response": {
                    "transaction_id": response.transaction_id,
                    "score": response.score,
                    "status": response.status,
                    "recommendations_count": len(response.recommendations),
                },
            }
            with open(golden_file, "w") as f:
                json.dump(golden_data, f, indent=2)

    def test_large_transaction_response(self, agent, golden_data_dir):
        """Test response for large transaction amount."""
        request = CheckoutRequest(
            merchant_id="large_merchant", amount=Decimal("1000.00"), currency="USD"
        )

        response = agent.process_checkout(request)

        # Basic structure validation
        assert response.transaction_id is not None
        assert response.score >= 0 and response.score <= 1
        assert response.status == "completed"
        assert isinstance(response.recommendations, list)

        # Save golden data if directory exists
        if golden_data_dir.exists():
            golden_file = golden_data_dir / "large_transaction_response.json"
            golden_data = {
                "request": {
                    "merchant_id": request.merchant_id,
                    "amount": str(request.amount),
                    "currency": request.currency,
                },
                "response": {
                    "transaction_id": response.transaction_id,
                    "score": response.score,
                    "status": response.status,
                    "recommendations_count": len(response.recommendations),
                },
            }
            with open(golden_file, "w") as f:
                json.dump(golden_data, f, indent=2)

    def test_consistent_recommendations_structure(self, agent):
        """Test that recommendations have consistent structure."""
        request = CheckoutRequest(
            merchant_id="test_merchant", amount=Decimal("100.00"), currency="USD"
        )

        response = agent.process_checkout(request)

        for rec in response.recommendations:
            assert "card_id" in rec
            assert "name" in rec
            assert "cashback_rate" in rec
            assert "reason" in rec
            assert isinstance(rec["cashback_rate"], (int, float))
            assert isinstance(rec["reason"], str)
