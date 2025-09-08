"""Comprehensive tests for the CLI module to improve coverage."""

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from click.testing import CliRunner

from altwallet_agent.cli import (
    cli,
    score,
    score_file,
    simulate_decision,
    webhook_history,
)


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


def create_mock_score_result():
    """Create a mock ScoreResult for testing."""
    from altwallet_agent.scoring import ScoreResult

    return ScoreResult(
        risk_score=20,
        loyalty_boost=5,
        final_score=85,
        routing_hint="VISA",
        signals={"test": "signal"},
    )


@pytest.fixture
def sample_context_file():
    """Create a temporary file with sample context data."""
    context_data = {
        "merchant": {"id": "amazon", "name": "Amazon", "mcc": "5411", "region": "US"},
        "customer": {
            "id": "cust_123",
            "loyalty_tier": "GOLD",
            "risk_score": 0.2,
            "chargebacks_12m": 0,
        },
        "device": {
            "ip": "192.168.1.1",
            "user_agent": "Mozilla/5.0",
            "network_preferences": [],
        },
        "transaction": {
            "amount": 150.00,
            "currency": "USD",
            "timestamp": "2024-01-01T12:00:00Z",
        },
        "cart": {
            "total": 150.00,
            "items": [
                {
                    "item": "Test Item",
                    "unit_price": 150.00,
                    "qty": 1,
                    "category": "electronics",
                }
            ],
        },
        "geo": {"country": "US", "region": "CA", "city": "San Francisco"},
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(context_data, f)
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    temp_path.unlink(missing_ok=True)


class TestCLIBasic:
    """Test basic CLI functionality."""

    def test_cli_help(self, runner):
        """Test CLI help command."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "AltWallet Checkout Agent CLI" in result.output

    def test_cli_version(self, runner):
        """Test CLI version option."""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0.3.0" in result.output

    def test_cli_no_command(self, runner):
        """Test CLI with no command."""
        result = runner.invoke(cli, [])
        assert result.exit_code == 2  # Click shows help and exits with code 2
        assert "AltWallet Checkout Agent CLI" in result.output


class TestScoreCommand:
    """Test the score command."""

    @patch("altwallet_agent.cli.score_transaction")
    @patch("altwallet_agent.cli.set_trace_id")
    @patch("altwallet_agent.cli.set_request_start_time")
    def test_score_with_input_file(
        self, mock_set_time, mock_set_trace, mock_score, runner, sample_context_file
    ):
        """Test score command with input file."""
        mock_score.return_value = create_mock_score_result()

        result = runner.invoke(score, ["--input", str(sample_context_file)])
        assert result.exit_code == 0
        assert "85" in result.output  # final_score
        assert "VISA" in result.output  # routing_hint

    @patch("altwallet_agent.cli.score_transaction")
    @patch("altwallet_agent.cli.set_trace_id")
    @patch("altwallet_agent.cli.set_request_start_time")
    def test_score_with_trace_id(
        self, mock_set_time, mock_set_trace, mock_score, runner, sample_context_file
    ):
        """Test score command with custom trace ID."""
        mock_score.return_value = create_mock_score_result()

        result = runner.invoke(
            score,
            ["--input", str(sample_context_file), "--trace-id", "custom-trace-123"],
        )
        assert result.exit_code == 0
        mock_set_trace.assert_called_with("custom-trace-123")

    @patch("altwallet_agent.cli.score_transaction")
    @patch("altwallet_agent.cli.set_trace_id")
    @patch("altwallet_agent.cli.set_request_start_time")
    def test_score_pretty_output(
        self, mock_set_time, mock_set_trace, mock_score, runner, sample_context_file
    ):
        """Test score command with pretty output."""
        mock_score.return_value = create_mock_score_result()

        result = runner.invoke(score, ["--input", str(sample_context_file), "--pretty"])
        assert result.exit_code == 0
        # Pretty output should be formatted JSON
        assert "final_score" in result.output

    @patch("altwallet_agent.cli.score_transaction")
    @patch("altwallet_agent.cli.set_trace_id")
    @patch("altwallet_agent.cli.set_request_start_time")
    def test_score_json_output(
        self, mock_set_time, mock_set_trace, mock_score, runner, sample_context_file
    ):
        """Test score command with JSON output."""
        mock_score.return_value = create_mock_score_result()

        result = runner.invoke(score, ["--input", str(sample_context_file), "--json"])
        assert result.exit_code == 0
        # Should output raw JSON with card recommendations
        assert "card_recommendations" in result.output

    @patch("altwallet_agent.cli.score_transaction")
    @patch("altwallet_agent.cli.set_trace_id")
    @patch("altwallet_agent.cli.set_request_start_time")
    def test_score_verbose(
        self, mock_set_time, mock_set_trace, mock_score, runner, sample_context_file
    ):
        """Test score command with verbose logging."""
        mock_score.return_value = create_mock_score_result()

        result = runner.invoke(
            score,
            [
                "--input",
                str(sample_context_file),
                "-vv",  # Use the correct verbose flag
            ],
        )
        assert result.exit_code == 0

    def test_score_invalid_file(self, runner):
        """Test score command with invalid file."""
        result = runner.invoke(score, ["--input", "nonexistent.json"])
        assert result.exit_code != 0
        assert "Error" in result.output or "not found" in result.output

    def test_score_missing_input(self, runner):
        """Test score command without input file."""
        result = runner.invoke(score, [])
        assert result.exit_code != 0


class TestSimulateDecisionCommand:
    """Test the simulate-decision command."""

    @patch("altwallet_agent.cli.log_decision_outcome")
    @patch("altwallet_agent.cli.set_trace_id")
    @patch("altwallet_agent.cli.set_request_start_time")
    def test_simulate_approve_decision(
        self, mock_set_time, mock_set_trace, mock_log, runner
    ):
        """Test simulating an approve decision."""
        result = runner.invoke(simulate_decision, ["--approve", "--analytics"])
        assert result.exit_code == 0
        assert "APPROVE" in result.output
        mock_log.assert_called_once()

    @patch("altwallet_agent.cli.log_decision_outcome")
    @patch("altwallet_agent.cli.set_trace_id")
    @patch("altwallet_agent.cli.set_request_start_time")
    def test_simulate_decline_decision(
        self, mock_set_time, mock_set_trace, mock_log, runner
    ):
        """Test simulating a decline decision."""
        result = runner.invoke(simulate_decision, ["--decline", "--analytics"])
        assert result.exit_code == 0
        assert "DECLINE" in result.output
        mock_log.assert_called_once()

    @patch("altwallet_agent.cli.log_decision_outcome")
    @patch("altwallet_agent.cli.set_trace_id")
    @patch("altwallet_agent.cli.set_request_start_time")
    def test_simulate_review_decision(
        self, mock_set_time, mock_set_trace, mock_log, runner
    ):
        """Test simulating a review decision."""
        result = runner.invoke(simulate_decision, ["--review", "--analytics"])
        assert result.exit_code == 0
        assert "REVIEW" in result.output
        mock_log.assert_called_once()

    @patch("altwallet_agent.cli.log_decision_outcome")
    @patch("altwallet_agent.cli.set_trace_id")
    @patch("altwallet_agent.cli.set_request_start_time")
    def test_simulate_with_discount_rule(
        self, mock_set_time, mock_set_trace, mock_log, runner
    ):
        """Test simulating with discount business rule."""
        result = runner.invoke(simulate_decision, ["--approve", "--discount"])
        assert result.exit_code == 0
        assert "APPROVE" in result.output
        assert "discount" in result.output.lower()

    @patch("altwallet_agent.cli.log_decision_outcome")
    @patch("altwallet_agent.cli.set_trace_id")
    @patch("altwallet_agent.cli.set_request_start_time")
    def test_simulate_with_kyc_rule(
        self, mock_set_time, mock_set_trace, mock_log, runner
    ):
        """Test simulating with KYC business rule."""
        result = runner.invoke(simulate_decision, ["--approve", "--kyc"])
        assert result.exit_code == 0
        assert "APPROVE" in result.output
        assert "kyc" in result.output.lower()

    @patch("altwallet_agent.cli.log_decision_outcome")
    @patch("altwallet_agent.cli.set_trace_id")
    @patch("altwallet_agent.cli.set_request_start_time")
    def test_simulate_with_custom_parameters(
        self, mock_set_time, mock_set_trace, mock_log, runner
    ):
        """Test simulating with custom parameters."""
        result = runner.invoke(
            simulate_decision,
            [
                "--approve",
                "--customer-id",
                "custom_cust_456",
                "--merchant-id",
                "custom_merch_789",
                "--amount",
                "250.50",
                "--mcc",
                "5812",
                "--region",
                "CA",
            ],
        )
        assert result.exit_code == 0
        assert "APPROVE" in result.output
        # The custom parameters are used internally but may not appear in the output
        # Check that the decision contract is properly formatted
        assert "Decision Contract:" in result.output

    @patch("altwallet_agent.cli.log_decision_outcome")
    @patch("altwallet_agent.cli.set_trace_id")
    @patch("altwallet_agent.cli.set_request_start_time")
    def test_simulate_no_decision_flag(
        self, mock_set_time, mock_set_trace, mock_log, runner
    ):
        """Test simulating without any decision flag (should show error)."""
        result = runner.invoke(simulate_decision, [])
        assert (
            result.exit_code == 0
        )  # Click doesn't set exit code for errors in this case
        assert "ERROR: Must specify exactly one decision flag" in result.output


class TestSimulateDecisionWithWebhooks:
    """Test simulate-decision command with webhook functionality."""

    @patch("altwallet_agent.cli._HAS_WEBHOOKS", True)
    @patch("altwallet_agent.cli.get_webhook_emitter")
    @patch("altwallet_agent.cli.log_decision_outcome")
    @patch("altwallet_agent.cli.set_trace_id")
    @patch("altwallet_agent.cli.set_request_start_time")
    def test_simulate_with_webhook(
        self, mock_set_time, mock_set_trace, mock_log, mock_get_emitter, runner
    ):
        """Test simulating with webhook enabled."""
        mock_emitter = AsyncMock()
        mock_get_emitter.return_value = mock_emitter

        result = runner.invoke(simulate_decision, ["--approve", "--webhook"])
        assert result.exit_code == 0
        assert "APPROVE" in result.output

    @patch("altwallet_agent.cli._HAS_WEBHOOKS", False)
    @patch("altwallet_agent.cli.log_decision_outcome")
    @patch("altwallet_agent.cli.set_trace_id")
    @patch("altwallet_agent.cli.set_request_start_time")
    def test_simulate_with_webhook_unavailable(
        self, mock_set_time, mock_set_trace, mock_log, runner
    ):
        """Test simulating with webhook when webhooks are unavailable."""
        result = runner.invoke(simulate_decision, ["--approve", "--webhook"])
        assert result.exit_code == 0
        assert "APPROVE" in result.output
        # Should not crash even if webhooks are unavailable


class TestSimulateDecisionWithAnalytics:
    """Test simulate-decision command with analytics."""

    @patch("altwallet_agent.cli.log_decision_outcome")
    @patch("altwallet_agent.cli.set_trace_id")
    @patch("altwallet_agent.cli.set_request_start_time")
    def test_simulate_with_analytics(
        self, mock_set_time, mock_set_trace, mock_log, runner
    ):
        """Test simulating with analytics enabled."""
        result = runner.invoke(simulate_decision, ["--approve", "--analytics"])
        assert result.exit_code == 0
        assert "APPROVE" in result.output
        mock_log.assert_called_once()


class TestScoreFileCommand:
    """Test the score-file command."""

    @patch("altwallet_agent.scoring.score_transaction")
    @patch("altwallet_agent.cli.set_trace_id")
    @patch("altwallet_agent.cli.set_request_start_time")
    def test_score_file_success(
        self, mock_set_time, mock_set_trace, mock_score, runner, sample_context_file
    ):
        """Test score-file command with valid file."""
        mock_score.return_value = create_mock_score_result()

        result = runner.invoke(score_file, ["--input", str(sample_context_file)])
        assert result.exit_code == 0
        assert "85" in result.output  # final_score from mocked result

    def test_score_file_missing_input(self, runner):
        """Test score-file command without input."""
        result = runner.invoke(score_file, [])
        assert result.exit_code != 0

    def test_score_file_invalid_file(self, runner):
        """Test score-file command with invalid file."""
        result = runner.invoke(score_file, ["--input", "nonexistent.json"])
        assert result.exit_code == 0  # score_file doesn't set exit code for errors
        assert "ERROR: Input file not found" in result.output


class TestWebhookHistoryCommand:
    """Test the webhook-history command."""

    @patch("altwallet_agent.cli._HAS_WEBHOOKS", True)
    @patch("altwallet_agent.cli.get_webhook_manager")
    def test_webhook_history_success(self, mock_get_manager, runner):
        """Test webhook-history command."""
        mock_manager = AsyncMock()
        mock_manager.get_delivery_stats.return_value = {
            "total_deliveries": 10,
            "successful_deliveries": 8,
            "failed_deliveries": 2,
            "success_rate": 0.8,
        }
        mock_get_manager.return_value = mock_manager

        result = runner.invoke(webhook_history, [])
        assert result.exit_code == 0

    @patch("altwallet_agent.cli._HAS_WEBHOOKS", True)
    @patch("altwallet_agent.cli.get_webhook_manager")
    def test_webhook_history_with_id(self, mock_get_manager, runner):
        """Test webhook-history command with specific webhook ID."""
        mock_manager = AsyncMock()
        mock_manager.get_delivery_stats.return_value = {
            "total_deliveries": 1,
            "successful_deliveries": 1,
            "failed_deliveries": 0,
            "success_rate": 1.0,
        }
        mock_get_manager.return_value = mock_manager

        result = runner.invoke(webhook_history, ["--webhook-id", "webhook_123"])
        assert result.exit_code == 0

    @patch("altwallet_agent.cli._HAS_WEBHOOKS", False)
    def test_webhook_history_unavailable(self, runner):
        """Test webhook-history command when webhooks are unavailable."""
        result = runner.invoke(webhook_history, [])
        assert result.exit_code == 0  # Click doesn't set exit code for exceptions
        assert "No webhook history found" in result.output


class TestCLIErrorHandling:
    """Test CLI error handling scenarios."""

    def test_score_with_invalid_json(self, runner):
        """Test score command with invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content")
            temp_path = Path(f.name)

        try:
            result = runner.invoke(score, ["--input", str(temp_path)])
            assert result.exit_code != 0
        finally:
            temp_path.unlink(missing_ok=True)

    @patch("altwallet_agent.cli.score_transaction")
    @patch("altwallet_agent.cli.set_trace_id")
    @patch("altwallet_agent.cli.set_request_start_time")
    def test_score_processing_error(
        self, mock_set_time, mock_set_trace, mock_score, runner, sample_context_file
    ):
        """Test score command with processing error."""
        mock_score.side_effect = Exception("Processing error")

        result = runner.invoke(score, ["--input", str(sample_context_file)])
        assert result.exit_code == 1  # Click sets exit code 1 for exceptions
        # When an exception occurs, Click doesn't print to stdout, just sets exit code

    @patch("altwallet_agent.cli.log_decision_outcome")
    @patch("altwallet_agent.cli.set_trace_id")
    @patch("altwallet_agent.cli.set_request_start_time")
    def test_simulate_decision_logging_error(
        self, mock_set_time, mock_set_trace, mock_log, runner
    ):
        """Test simulate-decision with logging error."""
        mock_log.side_effect = Exception("Logging error")

        result = runner.invoke(simulate_decision, ["--approve"])
        # Should still succeed even if logging fails
        assert result.exit_code == 0
        assert "APPROVE" in result.output


class TestCLIIntegration:
    """Test CLI integration scenarios."""

    @patch("altwallet_agent.cli.score_transaction")
    @patch("altwallet_agent.cli.set_trace_id")
    @patch("altwallet_agent.cli.set_request_start_time")
    def test_full_score_workflow(
        self, mock_set_time, mock_set_trace, mock_score, runner, sample_context_file
    ):
        """Test complete score workflow."""
        mock_score.return_value = create_mock_score_result()

        result = runner.invoke(
            score,
            [
                "--input",
                str(sample_context_file),
                "--trace-id",
                "integration-test-123",
                "--pretty",
            ],
        )

        assert result.exit_code == 0
        assert "85" in result.output  # final_score from mocked result
        assert "VISA" in result.output  # routing_hint

    @patch("altwallet_agent.cli.log_decision_outcome")
    @patch("altwallet_agent.cli.set_trace_id")
    @patch("altwallet_agent.cli.set_request_start_time")
    def test_full_simulation_workflow(
        self, mock_set_time, mock_set_trace, mock_log, runner
    ):
        """Test complete simulation workflow."""
        result = runner.invoke(
            simulate_decision,
            [
                "--approve",
                "--discount",
                "--kyc",
                "--customer-id",
                "integration_cust_789",
                "--merchant-id",
                "integration_merch_456",
                "--amount",
                "500.00",
                "--mcc",
                "5814",
                "--region",
                "EU",
                "--analytics",
            ],
        )

        assert result.exit_code == 0
        assert "APPROVE" in result.output
        assert "Decision Contract:" in result.output
        mock_log.assert_called_once()


class TestCLIPerformance:
    """Test CLI performance characteristics."""

    @patch("altwallet_agent.cli.score_transaction")
    @patch("altwallet_agent.cli.set_trace_id")
    @patch("altwallet_agent.cli.set_request_start_time")
    def test_score_performance(
        self, mock_set_time, mock_set_trace, mock_score, runner, sample_context_file
    ):
        """Test score command performance."""
        import time

        mock_score.return_value = create_mock_score_result()

        start_time = time.time()
        result = runner.invoke(score, ["--input", str(sample_context_file)])
        end_time = time.time()

        assert result.exit_code == 0
        # Should complete within reasonable time (less than 5 seconds)
        assert (end_time - start_time) < 5.0

    @patch("altwallet_agent.cli.log_decision_outcome")
    @patch("altwallet_agent.cli.set_trace_id")
    @patch("altwallet_agent.cli.set_request_start_time")
    def test_simulation_performance(
        self, mock_set_time, mock_set_trace, mock_log, runner
    ):
        """Test simulation command performance."""
        import time

        start_time = time.time()
        result = runner.invoke(simulate_decision, ["--approve"])
        end_time = time.time()

        assert result.exit_code == 0
        # Should complete within reasonable time (less than 2 seconds)
        assert (end_time - start_time) < 2.0
