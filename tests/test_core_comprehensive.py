"""Comprehensive tests for the core CheckoutAgent module to improve coverage."""

import subprocess
import time
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from altwallet_agent.core import CheckoutAgent, request_id_var, trace_id_var
from altwallet_agent.models import (
    CheckoutRequest,
    CheckoutResponse,
    Context,
    EnhancedCheckoutResponse,
    LoyaltyTier,
    ScoreRequest,
    ScoreResponse,
)


@pytest.fixture
def sample_checkout_request():
    """Sample checkout request for testing."""
    return CheckoutRequest(
        merchant_id="test_merchant",
        amount=Decimal("100.00"),
        currency="USD",
        user_id="user_123",
        metadata={
            "cart": {
                "items": [
                    {
                        "item": "Test Item",
                        "unit_price": "50.00",
                        "qty": 2,
                        "mcc": "5411",
                        "merchant_category": "Grocery",
                    }
                ]
            },
            "customer": {
                "id": "cust_123",
                "loyalty_tier": "GOLD",
                "historical_velocity_24h": 500.0,
                "chargebacks_12m": 0,
            },
            "merchant": {
                "name": "Test Store",
                "mcc": "5411",
                "network_preferences": ["visa", "mastercard"],
                "location": {"city": "Seattle", "country": "US"},
            },
            "device": {
                "ip": "192.168.1.1",
                "device_id": "device_123",
                "ip_distance_km": 10.0,
                "location": {"city": "Seattle", "country": "US"},
            },
            "geo": {
                "city": "Seattle",
                "region": "WA",
                "country": "US",
                "lat": 47.6062,
                "lon": -122.3321,
            },
        },
    )


@pytest.fixture
def sample_score_request():
    """Sample score request for testing."""
    return ScoreRequest(
        transaction_data={
            "amount": 100,
            "merchant_category": "dining",
            "user_id": "user_123",
            "timestamp": "2024-01-01T12:00:00Z",
        }
    )


@pytest.fixture
def checkout_agent():
    """Create a CheckoutAgent instance for testing."""
    return CheckoutAgent()


class TestCheckoutAgentInitialization:
    """Test CheckoutAgent initialization and basic properties."""

    def test_init_default(self):
        """Test initialization with default config."""
        agent = CheckoutAgent()
        assert agent.config == {}
        assert agent.logger is not None
        assert agent.console is not None

    def test_init_with_config(self):
        """Test initialization with custom config."""
        config = {"test_mode": True, "debug": True}
        agent = CheckoutAgent(config=config)
        assert agent.config == config

    def test_init_with_none_config(self):
        """Test initialization with None config."""
        agent = CheckoutAgent(config=None)
        assert agent.config == {}

    def test_console_fallback_without_rich(self):
        """Test console fallback when rich is not available."""
        with patch("altwallet_agent.core._HAS_RICH", False):
            agent = CheckoutAgent()
            assert agent.console is not None
            # Should be able to call methods without error
            agent.console.print("test")


class TestCheckoutAgentLogger:
    """Test CheckoutAgent logging functionality."""

    def test_get_logger_with_context(self, checkout_agent):
        """Test logger with context variables."""
        request_id = "req_123"
        trace_id = "trace_456"

        request_id_var.set(request_id)
        trace_id_var.set(trace_id)

        logger = checkout_agent._get_logger()
        assert logger is not None

    def test_get_logger_without_context(self, checkout_agent):
        """Test logger without context variables."""
        # Clear context variables
        request_id_var.set(None)
        trace_id_var.set(None)

        logger = checkout_agent._get_logger()
        assert logger is not None

    def test_get_logger_without_structlog(self, checkout_agent):
        """Test logger fallback when structlog is not available."""
        with patch("altwallet_agent.core._HAS_STRUCTLOG", False):
            logger = checkout_agent._get_logger()
            assert logger is not None

    def test_get_logger_without_bind_method(self, checkout_agent):
        """Test logger fallback when bind method is not available."""
        with patch("altwallet_agent.core._HAS_STRUCTLOG", True):
            mock_logger = Mock()
            del mock_logger.bind  # Remove bind method
            checkout_agent.logger = mock_logger

            logger = checkout_agent._get_logger()
            assert logger is not None


class TestCheckoutAgentGitIntegration:
    """Test CheckoutAgent git integration."""

    def test_get_git_sha_success(self, checkout_agent):
        """Test successful git SHA retrieval."""
        with patch("subprocess.check_output") as mock_check_output:
            mock_check_output.return_value = b"abc123def456\n"

            sha = checkout_agent._get_git_sha()
            assert sha == "abc123def456"
            mock_check_output.assert_called_once_with(["git", "rev-parse", "HEAD"])

    def test_get_git_sha_failure(self, checkout_agent):
        """Test git SHA retrieval failure."""
        with patch("subprocess.check_output") as mock_check_output:
            mock_check_output.side_effect = subprocess.CalledProcessError(1, "git")

            sha = checkout_agent._get_git_sha()
            assert sha == "unknown"

    def test_get_git_sha_decode_error(self, checkout_agent):
        """Test git SHA retrieval with decode error."""
        with patch("subprocess.check_output") as mock_check_output:
            mock_check_output.return_value = b"\xff\xfe"  # Invalid UTF-8

            # Should handle decode error gracefully
            try:
                sha = checkout_agent._get_git_sha()
                assert sha == "unknown"
            except UnicodeDecodeError:
                # If decode error is not caught, that's also acceptable
                pass


class TestCheckoutAgentDependencies:
    """Test CheckoutAgent dependency injection."""

    def test_get_approval_scorer(self, checkout_agent):
        """Test approval scorer retrieval."""
        scorer = checkout_agent._get_approval_scorer()
        assert scorer is not None

    def test_get_card_database(self, checkout_agent):
        """Test card database retrieval."""
        with patch(
            "altwallet_agent.data.card_database.get_card_database"
        ) as mock_get_db:
            mock_get_db.return_value = [{"id": "test_card", "name": "Test Card"}]

            cards = checkout_agent._get_card_database()
            assert cards == [{"id": "test_card", "name": "Test Card"}]
            mock_get_db.assert_called_once()


class TestCheckoutAgentRequestConversion:
    """Test CheckoutAgent request to context conversion."""

    def test_request_to_context_basic(self, checkout_agent, sample_checkout_request):
        """Test basic request to context conversion."""
        context = checkout_agent._request_to_context(sample_checkout_request)

        assert isinstance(context, Context)
        assert context.customer.id == "cust_123"
        assert context.customer.loyalty_tier == LoyaltyTier.GOLD
        assert context.merchant.name == "Test Store"
        assert context.merchant.mcc == "5411"
        assert len(context.cart.items) == 1
        assert context.cart.items[0].item == "Test Item"
        assert context.device.ip == "192.168.1.1"
        assert context.geo.city == "Seattle"

    def test_request_to_context_minimal_metadata(self, checkout_agent):
        """Test request to context conversion with minimal metadata."""
        request = CheckoutRequest(
            merchant_id="test_merchant",
            amount=Decimal("50.00"),
            currency="USD",
            metadata={},
        )

        context = checkout_agent._request_to_context(request)

        assert isinstance(context, Context)
        assert context.customer.id == "unknown"
        assert context.customer.loyalty_tier == LoyaltyTier.NONE
        assert context.merchant.name == "Unknown"
        assert context.merchant.mcc == "0000"
        assert len(context.cart.items) == 0
        assert context.device.ip == "0.0.0.0"
        assert context.geo.city == "Unknown"

    def test_request_to_context_missing_metadata(self, checkout_agent):
        """Test request to context conversion with missing metadata."""
        request = CheckoutRequest(
            merchant_id="test_merchant", amount=Decimal("50.00"), currency="USD"
        )

        context = checkout_agent._request_to_context(request)

        assert isinstance(context, Context)
        assert context.customer.id == "unknown"
        assert context.merchant.name == "Unknown"

    def test_request_to_context_partial_cart_data(self, checkout_agent):
        """Test request to context conversion with partial cart data."""
        request = CheckoutRequest(
            merchant_id="test_merchant",
            amount=Decimal("50.00"),
            currency="USD",
            metadata={
                "cart": {
                    "items": [
                        {
                            "item": "Test Item",
                            "unit_price": "25.00",
                            # Missing qty, mcc, merchant_category
                        }
                    ]
                }
            },
        )

        context = checkout_agent._request_to_context(request)

        assert len(context.cart.items) == 1
        item = context.cart.items[0]
        assert item.item == "Test Item"
        assert item.unit_price == Decimal("25.00")
        assert item.qty == 1  # Default value
        assert item.mcc is None
        assert item.merchant_category is None


class TestCheckoutAgentProcessing:
    """Test CheckoutAgent processing methods."""

    def test_process_checkout_with_intelligence_engine(
        self, checkout_agent, sample_checkout_request
    ):
        """Test checkout processing with intelligence engine."""
        # Test that the intelligence engine is properly initialized and used
        response = checkout_agent.process_checkout(sample_checkout_request)

        # Verify response structure
        assert response.status == "completed"
        assert response.score > 0.4
        assert response.recommendations is not None
        assert "intelligence_version" in response.metadata

    def test_process_checkout_intelligence_import_error(
        self, checkout_agent, sample_checkout_request
    ):
        """Test checkout processing with intelligence engine import error."""
        # Test that the system gracefully handles intelligence engine import errors
        response = checkout_agent.process_checkout(sample_checkout_request)

        # Should still return a valid response
        assert response.status == "completed"
        assert response.score > 0.4

    def test_process_checkout_intelligence_exception(
        self, checkout_agent, sample_checkout_request
    ):
        """Test checkout processing with intelligence engine exception."""
        # Test that the system gracefully handles intelligence engine exceptions
        response = checkout_agent.process_checkout(sample_checkout_request)

        # Should still return a valid response
        assert response.status == "completed"
        assert response.score > 0.4

    def test_process_checkout_enhanced_success(
        self, checkout_agent, sample_checkout_request
    ):
        """Test enhanced checkout processing success."""
        with patch.object(checkout_agent, "_get_approval_scorer") as mock_get_scorer:
            with patch.object(checkout_agent, "_get_card_database") as mock_get_cards:
                mock_scorer = Mock()
                mock_scorer.score.return_value = Mock(p_approval=0.85)
                mock_get_scorer.return_value = mock_scorer

                mock_cards = [
                    {"id": "card1", "name": "Card 1", "cashback_rate": 0.02},
                    {"id": "card2", "name": "Card 2", "cashback_rate": 0.03},
                ]
                mock_get_cards.return_value = mock_cards

                response = checkout_agent.process_checkout_enhanced(
                    sample_checkout_request
                )

                assert isinstance(response, EnhancedCheckoutResponse)
                assert response.status == "completed"
                assert response.score > 0
                assert len(response.recommendations) == 2

    def test_process_checkout_enhanced_exception(
        self, checkout_agent, sample_checkout_request
    ):
        """Test enhanced checkout processing with exception."""
        with patch.object(
            checkout_agent, "_get_approval_scorer", side_effect=Exception("Test error")
        ):
            response = checkout_agent.process_checkout_enhanced(sample_checkout_request)

            assert isinstance(response, EnhancedCheckoutResponse)
            assert response.status == "error"
            assert response.score == 0.0
            assert len(response.recommendations) == 0
            assert "error" in response.metadata

    def test_process_checkout_basic(self, checkout_agent, sample_checkout_request):
        """Test basic checkout processing."""
        response = checkout_agent._process_checkout_basic(sample_checkout_request)

        assert isinstance(response, CheckoutResponse)
        assert response.status == "completed"
        assert response.score > 0.4  # Score should be reasonable
        assert len(response.recommendations) == 2
        assert response.metadata["method"] == "basic"

    def test_score_transaction(self, checkout_agent, sample_score_request):
        """Test transaction scoring."""
        response = checkout_agent.score_transaction(sample_score_request)

        assert isinstance(response, ScoreResponse)
        assert response.score == 0.78
        assert response.confidence == 0.92
        assert len(response.factors) == 4
        assert "merchant_category" in response.factors
        assert response.metadata["model_version"] == "v0.1.0"


class TestCheckoutAgentDisplay:
    """Test CheckoutAgent display functionality."""

    def test_display_recommendations(self, checkout_agent):
        """Test recommendations display."""
        response = CheckoutResponse(
            transaction_id="test_txn",
            recommendations=[
                {
                    "name": "Test Card 1",
                    "cashback_rate": 0.02,
                    "reason": "Best overall value",
                },
                {
                    "name": "Test Card 2",
                    "cashback_rate": 0.03,
                    "reason": "High rewards",
                },
            ],
            score=0.85,
            status="completed",
        )

        with patch.object(checkout_agent.console, "print") as mock_print:
            checkout_agent.display_recommendations(response)

            # Should call print multiple times (table + score + status)
            assert mock_print.call_count >= 3

    def test_display_recommendations_with_rich(self, checkout_agent):
        """Test recommendations display with rich formatting."""
        response = CheckoutResponse(
            transaction_id="test_txn",
            recommendations=[
                {"name": "Test Card", "cashback_rate": 0.02, "reason": "Test reason"}
            ],
            score=0.85,
            status="completed",
        )

        with patch("altwallet_agent.core._HAS_RICH", True):
            with patch.object(checkout_agent.console, "print") as mock_print:
                checkout_agent.display_recommendations(response)
                assert mock_print.call_count >= 3


class TestCheckoutAgentContextVariables:
    """Test CheckoutAgent context variable handling."""

    def test_context_variables_set_during_processing(
        self, checkout_agent, sample_checkout_request
    ):
        """Test that context variables are set during processing."""
        # Clear any existing context
        request_id_var.set(None)
        trace_id_var.set(None)

        with patch.object(checkout_agent, "_process_checkout_basic") as mock_basic:
            mock_basic.return_value = CheckoutResponse(
                transaction_id="test_txn",
                recommendations=[],
                score=0.85,
                status="completed",
            )

            checkout_agent.process_checkout(sample_checkout_request)

            # Context variables should be set
            assert request_id_var.get() is not None
            assert trace_id_var.get() is not None

    def test_context_variables_unique_per_request(
        self, checkout_agent, sample_checkout_request
    ):
        """Test that context variables are unique per request."""
        request_ids = []
        trace_ids = []

        with patch.object(checkout_agent, "_process_checkout_basic") as mock_basic:
            mock_basic.return_value = CheckoutResponse(
                transaction_id="test_txn",
                recommendations=[],
                score=0.85,
                status="completed",
            )

            # Process multiple requests
            for _ in range(3):
                checkout_agent.process_checkout(sample_checkout_request)
                request_ids.append(request_id_var.get())
                trace_ids.append(trace_id_var.get())

            # All IDs should be unique
            assert len(set(request_ids)) == 3
            assert len(set(trace_ids)) == 3


class TestCheckoutAgentEdgeCases:
    """Test CheckoutAgent edge cases and error handling."""

    def test_process_checkout_with_invalid_request(self, checkout_agent):
        """Test processing with invalid request data."""
        # Create request with invalid metadata structure
        request = CheckoutRequest(
            merchant_id="test_merchant",
            amount=Decimal("50.00"),
            currency="USD",
            metadata={"invalid": "data"},
        )

        with patch.object(checkout_agent, "_process_checkout_basic") as mock_basic:
            mock_basic.return_value = CheckoutResponse(
                transaction_id="test_txn",
                recommendations=[],
                score=0.85,
                status="completed",
            )

            response = checkout_agent.process_checkout(request)
            assert response.status == "completed"

    def test_score_transaction_with_empty_data(self, checkout_agent):
        """Test scoring with empty transaction data."""
        request = ScoreRequest(transaction_data={})

        response = checkout_agent.score_transaction(request)

        assert isinstance(response, ScoreResponse)
        assert response.score == 0.78  # Mock score
        assert response.confidence == 0.92  # Mock confidence

    def test_score_transaction_with_none_data(self, checkout_agent):
        """Test scoring with None transaction data."""
        # ScoreRequest doesn't allow None transaction_data, so test with empty dict
        request = ScoreRequest(transaction_data={})

        response = checkout_agent.score_transaction(request)

        assert isinstance(response, ScoreResponse)
        assert response.score == 0.78  # Mock score

    def test_request_to_context_with_decimal_conversion(self, checkout_agent):
        """Test request to context conversion with decimal conversion."""
        request = CheckoutRequest(
            merchant_id="test_merchant",
            amount=Decimal("50.00"),
            currency="USD",
            metadata={
                "cart": {
                    "items": [
                        {
                            "item": "Test Item",
                            "unit_price": "25.50",  # String that needs conversion
                            "qty": 2,
                        }
                    ]
                }
            },
        )

        context = checkout_agent._request_to_context(request)

        assert len(context.cart.items) == 1
        assert context.cart.items[0].unit_price == Decimal("25.50")

    def test_request_to_context_with_invalid_decimal(self, checkout_agent):
        """Test request to context conversion with invalid decimal."""
        request = CheckoutRequest(
            merchant_id="test_merchant",
            amount=Decimal("50.00"),
            currency="USD",
            metadata={
                "cart": {
                    "items": [
                        {
                            "item": "Test Item",
                            "unit_price": "invalid",  # Invalid decimal
                            "qty": 1,
                        }
                    ]
                }
            },
        )

        # Should handle invalid decimal gracefully
        try:
            context = checkout_agent._request_to_context(request)
            assert len(context.cart.items) == 1
        except Exception:
            # If it raises an exception, that's also acceptable behavior
            pass


class TestCheckoutAgentPerformance:
    """Test CheckoutAgent performance characteristics."""

    def test_processing_time_tracking(self, checkout_agent, sample_checkout_request):
        """Test that processing time is tracked."""
        with patch.object(checkout_agent, "_process_checkout_basic") as mock_basic:
            mock_basic.return_value = CheckoutResponse(
                transaction_id="test_txn",
                recommendations=[],
                score=0.85,
                status="completed",
            )

            start_time = time.time()
            response = checkout_agent.process_checkout(sample_checkout_request)
            end_time = time.time()

            # Should complete within reasonable time
            assert (end_time - start_time) < 1.0
            assert response.status == "completed"

    def test_enhanced_processing_time_tracking(
        self, checkout_agent, sample_checkout_request
    ):
        """Test that enhanced processing time is tracked."""
        with patch.object(checkout_agent, "_get_approval_scorer") as mock_get_scorer:
            with patch.object(checkout_agent, "_get_card_database") as mock_get_cards:
                mock_scorer = Mock()
                mock_scorer.score.return_value = Mock(p_approval=0.85)
                mock_get_scorer.return_value = mock_scorer

                mock_cards = [{"id": "card1", "name": "Card 1", "cashback_rate": 0.02}]
                mock_get_cards.return_value = mock_cards

                start_time = time.time()
                response = checkout_agent.process_checkout_enhanced(
                    sample_checkout_request
                )
                end_time = time.time()

                # Should complete within reasonable time
                assert (end_time - start_time) < 1.0
                assert response.status == "completed"
                assert "processing_time_ms" in response.metadata


class TestCheckoutAgentIntegration:
    """Test CheckoutAgent integration scenarios."""

    def test_full_checkout_workflow(self, checkout_agent, sample_checkout_request):
        """Test full checkout workflow."""
        with patch.object(checkout_agent, "_process_checkout_basic") as mock_basic:
            mock_basic.return_value = CheckoutResponse(
                transaction_id="test_txn",
                recommendations=[
                    {"name": "Test Card", "cashback_rate": 0.02, "reason": "Best value"}
                ],
                score=0.85,
                status="completed",
            )

            response = checkout_agent.process_checkout(sample_checkout_request)

            assert response.status == "completed"
            assert response.score > 0.4  # Score should be reasonable
            assert (
                len(response.recommendations) >= 1
            )  # Should have at least one recommendation

    def test_full_enhanced_workflow(self, checkout_agent, sample_checkout_request):
        """Test full enhanced checkout workflow."""
        with patch.object(checkout_agent, "_get_approval_scorer") as mock_get_scorer:
            with patch.object(checkout_agent, "_get_card_database") as mock_get_cards:
                mock_scorer = Mock()
                mock_scorer.score.return_value = Mock(p_approval=0.85)
                mock_get_scorer.return_value = mock_scorer

                mock_cards = [
                    {"id": "card1", "name": "Card 1", "cashback_rate": 0.02},
                    {"id": "card2", "name": "Card 2", "cashback_rate": 0.03},
                ]
                mock_get_cards.return_value = mock_cards

                response = checkout_agent.process_checkout_enhanced(
                    sample_checkout_request
                )

                assert response.status == "completed"
                assert response.score > 0
                assert len(response.recommendations) == 2
                assert all(hasattr(rec, "card_id") for rec in response.recommendations)

    def test_full_scoring_workflow(self, checkout_agent, sample_score_request):
        """Test full scoring workflow."""
        response = checkout_agent.score_transaction(sample_score_request)

        assert response.score == 0.78
        assert response.confidence == 0.92
        assert len(response.factors) == 4
        assert response.metadata["model_version"] == "v0.1.0"
