"""Smoke tests for AltWallet Checkout Agent."""

import pytest
from decimal import Decimal

from altwallet_agent import CheckoutAgent
from altwallet_agent.models import CheckoutRequest, ScoreRequest


def test_agent_initialization():
    """Test that the agent can be initialized."""
    agent = CheckoutAgent()
    assert agent is not None
    assert hasattr(agent, "process_checkout")
    assert hasattr(agent, "score_transaction")


def test_checkout_request_validation():
    """Test checkout request validation."""
    request = CheckoutRequest(
        merchant_id="test_merchant", amount=Decimal("100.50"), currency="USD"
    )
    assert request.merchant_id == "test_merchant"
    assert request.amount == Decimal("100.50")
    assert request.currency == "USD"


def test_score_request_validation():
    """Test score request validation."""
    request = ScoreRequest(transaction_data={"amount": 100, "merchant": "test"})
    assert request.transaction_data["amount"] == 100
    assert request.transaction_data["merchant"] == "test"


def test_checkout_processing():
    """Test basic checkout processing."""
    agent = CheckoutAgent()
    request = CheckoutRequest(
        merchant_id="test_merchant", amount=Decimal("50.00"), currency="USD"
    )

    response = agent.process_checkout(request)

    assert response.transaction_id is not None
    assert response.score >= 0 and response.score <= 1
    assert response.status == "completed"
    assert isinstance(response.recommendations, list)


def test_transaction_scoring():
    """Test basic transaction scoring."""
    agent = CheckoutAgent()
    request = ScoreRequest(
        transaction_data={"amount": 100, "merchant_category": "dining"}
    )

    response = agent.score_transaction(request)

    assert response.score >= 0 and response.score <= 1
    assert response.confidence >= 0 and response.confidence <= 1
    assert isinstance(response.factors, list)


def test_agent_with_config():
    """Test agent initialization with configuration."""
    config = {"test_mode": True, "debug": True}
    agent = CheckoutAgent(config=config)
    assert agent.config == config


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
