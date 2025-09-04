"""Smoke tests for AltWallet Checkout Agent."""

import json
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

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


def test_cli_with_context_basic():
    """Test CLI with examples/context_basic.json produces valid JSON."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    context_file = project_root / "examples" / "context_basic.json"

    assert context_file.exists(), f"Context file not found: {context_file}"

    try:
        # Run the CLI command
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "altwallet_agent",
                "score",
                "--input",
                str(context_file),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=project_root,
            check=True,
        )

        # Extract the JSON output from stdout (stderr contains log messages)
        lines = result.stdout.strip().split("\n")
        
        # Join all lines to reconstruct the complete JSON
        json_content = "\n".join(lines)

        # Parse the JSON output
        output_data = json.loads(json_content)

        # Assert it has the required fields
        assert "final_score" in output_data, "Missing final_score field"
        assert "risk_score" in output_data, "Missing risk_score field"
        assert "loyalty_boost" in output_data, "Missing loyalty_boost field"
        assert "routing_hint" in output_data, "Missing routing_hint field"
        assert "signals" in output_data, "Missing signals field"

        # Assert score values are reasonable
        assert isinstance(
            output_data["final_score"], (int, float)
        ), "final_score numeric"
        assert isinstance(output_data["risk_score"], (int, float)), "risk_score numeric"
        assert isinstance(
            output_data["loyalty_boost"], (int, float)
        ), "loyalty_boost numeric"

        # Assert score ranges
        assert 0 <= output_data["risk_score"] <= 100, "risk_score should be 0-100"
        assert 0 <= output_data["loyalty_boost"] <= 20, "loyalty_boost should be 0-20"
        assert 0 <= output_data["final_score"] <= 120, "final_score should be 0-120"

        # Assert signals is a dictionary
        assert isinstance(output_data["signals"], dict), "signals should be dict"

    except subprocess.CalledProcessError as e:
        pytest.fail(f"CLI command failed: {e.stderr}")
    except json.JSONDecodeError as e:
        pytest.fail(f"Failed to parse JSON output: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
