"""Tests for AltWallet Merchant Agent."""

import pytest
import click
from decimal import Decimal
from unittest.mock import patch
import sys
import os

# Add the package to the path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from altwallet_merchant_agent.core import CardRecommender, Purchase, Card
from altwallet_merchant_agent.cli import get_demo_card


class TestCardRecommender:
    """Test the card recommendation engine."""

    def test_grocery_purchase_recommends_amex(self):
        """Test that grocery purchases recommend Amex Blue Cash Preferred."""
        recommender = CardRecommender()
        purchase = Purchase(
            amount=Decimal("200.00"), category="groceries", merchant="Kroger"
        )

        best_card = recommender.get_best_card(purchase)
        assert best_card.name == "Amex Blue Cash Preferred"

    def test_travel_purchase_recommends_chase_sapphire(self):
        """Test that travel purchases recommend Chase Sapphire Preferred."""
        recommender = CardRecommender()
        purchase = Purchase(
            amount=Decimal("3000.00"), category="travel", merchant="Delta Airlines"
        )

        best_card = recommender.get_best_card(purchase)
        assert best_card.name == "Chase Sapphire Preferred"

    def test_general_purchase_recommends_citi_double_cash(self):
        """Test that general purchases recommend Citi Double Cash (highest base rate)."""
        recommender = CardRecommender()
        purchase = Purchase(
            amount=Decimal("50.00"), category="general", merchant="Amazon"
        )

        best_card = recommender.get_best_card(purchase)
        assert best_card.name == "Citi Double Cash"

    def test_large_purchase_with_annual_fee_consideration(self):
        """Test that annual fees are considered for large purchases."""
        recommender = CardRecommender()
        purchase = Purchase(
            amount=Decimal("1000.00"), category="general", merchant="Best Buy"
        )

        best_card = recommender.get_best_card(purchase)
        # For large purchases, Citi Double Cash should win due to higher base rate
        assert best_card.name == "Citi Double Cash"

    def test_apply_p_approval(self):
        """Test the p_approval enhancement method."""
        recommender = CardRecommender()

        # Test normal case
        result = recommender.apply_p_approval(10.0, 0.8)
        assert result == 8.0

        # Test edge cases
        result = recommender.apply_p_approval(10.0, 1.0)
        assert result == 10.0

        result = recommender.apply_p_approval(10.0, 0.0)
        assert result == 0.0

    def test_apply_p_approval_validation(self):
        """Test p_approval validation in core method."""
        recommender = CardRecommender()

        # Test invalid values
        with pytest.raises(ValueError, match="p_approval must be between 0 and 1"):
            recommender.apply_p_approval(10.0, 1.5)

        with pytest.raises(ValueError, match="p_approval must be between 0 and 1"):
            recommender.apply_p_approval(10.0, -0.1)

    def test_apply_geo_promo(self):
        """Test the geo_promo enhancement method."""
        recommender = CardRecommender()

        # Test normal case
        result = recommender.apply_geo_promo(Decimal("10.00"))
        assert result == Decimal("11.50")

        # Test with zero
        result = recommender.apply_geo_promo(Decimal("0.00"))
        assert result == Decimal("1.50")

        # Test with negative value
        result = recommender.apply_geo_promo(Decimal("-5.00"))
        assert result == Decimal("-3.50")


class TestPurchase:
    """Test the Purchase dataclass."""

    def test_purchase_creation(self):
        """Test creating a purchase object."""
        purchase = Purchase(
            amount=Decimal("75.50"), category="restaurants", merchant="Chipotle"
        )

        assert purchase.amount == Decimal("75.50")
        assert purchase.category == "restaurants"
        assert purchase.merchant == "Chipotle"


class TestCard:
    """Test the Card dataclass."""

    def test_card_creation(self):
        """Test creating a card object."""
        card = Card(
            name="Test Card",
            cashback_rate=Decimal("0.02"),
            annual_fee=Decimal("95"),
            category_bonus="gas",
            category_multiplier=Decimal("3.0"),
        )

        assert card.name == "Test Card"
        assert card.cashback_rate == Decimal("0.02")
        assert card.annual_fee == Decimal("95")
        assert card.category_bonus == "gas"
        assert card.category_multiplier == Decimal("3.0")

    def test_card_default_values(self):
        """Test card creation with default values."""
        card = Card(
            name="Basic Card", cashback_rate=Decimal("0.01"), annual_fee=Decimal("0")
        )

        assert card.category_bonus is None
        assert card.category_multiplier == Decimal("1.0")


class TestDemoCommand:
    """Test the demo command functionality."""

    def test_demo_card_selection_grocery(self):
        """Test that grocery merchants return Amex Blue Cash Preferred."""
        card = get_demo_card("Whole Foods")
        assert card == "Amex Blue Cash Preferred"

        card = get_demo_card("Kroger Market")
        assert card == "Amex Blue Cash Preferred"

        card = get_demo_card("Fresh Groceries")
        assert card == "Amex Blue Cash Preferred"

    def test_demo_card_selection_travel(self):
        """Test that travel merchants return Chase Sapphire Preferred."""
        card = get_demo_card("Delta Airlines")
        assert card == "Chase Sapphire Preferred"

        card = get_demo_card("Hilton Hotel")
        assert card == "Chase Sapphire Preferred"

        card = get_demo_card("Expedia Booking")
        assert card == "Chase Sapphire Preferred"

    def test_demo_card_selection_gas(self):
        """Test that gas merchants return Chase Freedom Unlimited."""
        card = get_demo_card("Shell Gas Station")
        assert card == "Chase Freedom Unlimited"

        card = get_demo_card("Exxon Fuel")
        assert card == "Chase Freedom Unlimited"

    def test_demo_card_selection_default(self):
        """Test that other merchants return Citi Double Cash."""
        card = get_demo_card("Amazon")
        assert card == "Citi Double Cash"

        card = get_demo_card("Best Buy")
        assert card == "Citi Double Cash"

        card = get_demo_card("Walmart")
        assert card == "Citi Double Cash"

    def test_demo_context_creation(self):
        """Test creating a context for merchant='Whole Foods', amount=180.0, location='New York'."""
        from altwallet_merchant_agent.cli import demo

        # Mock the console.print to capture output
        with patch("altwallet_merchant_agent.cli.console.print") as mock_print:
            # Call demo function directly with explicit values
            demo(
                merchant="Whole Foods",
                amount=180.0,
                location="New York",
                json_output=True,
                verbose=False,
                p_approval=0.95,
                geo_promo=False,
            )

            # Verify that console.print was called
            assert mock_print.called

            # Get the JSON output
            call_args = mock_print.call_args[0][0]

            # Parse the JSON output
            import json

            result = json.loads(call_args)

            # Validate the structure
            assert "recommended_card" in result
            assert "score" in result
            assert "signals" in result

            # Validate recommended_card is a non-empty string
            assert isinstance(result["recommended_card"], str)
            assert len(result["recommended_card"]) > 0
            assert result["recommended_card"] == "Amex Blue Cash Preferred"

            # Validate score is a float (now multiplied by default p_approval of 0.95)
            assert isinstance(result["score"], float)
            assert result["score"] == 5.13  # 180 * 0.03 * 0.95

            # Validate signals contains all required fields (including new enhancement fields)
            signals = result["signals"]
            assert "merchant" in signals
            assert "location" in signals
            assert "rewards_value_usd" in signals
            assert "merchant_penalty_usd" in signals
            assert "p_approval_used" in signals
            assert "geo_promo_applied" in signals

            # Validate signal values
            assert signals["merchant"] == "Whole Foods"
            assert signals["location"] == "New York"
            assert signals["rewards_value_usd"] == 5.4
            assert signals["merchant_penalty_usd"] == 0.0
            assert signals["p_approval_used"] == 0.95
            assert signals["geo_promo_applied"] is False

    def test_deterministic_scores(self):
        """Test that scores are deterministic for the same inputs."""
        from altwallet_merchant_agent.cli import demo

        with patch("altwallet_merchant_agent.cli.console.print") as mock_print:
            # Call demo function twice with same inputs
            demo(
                merchant="Whole Foods",
                amount=180.0,
                location="New York",
                json_output=True,
                verbose=False,
                p_approval=0.95,
                geo_promo=False,
            )
            first_call = mock_print.call_args[0][0]

            mock_print.reset_mock()

            demo(
                merchant="Whole Foods",
                amount=180.0,
                location="New York",
                json_output=True,
                verbose=False,
                p_approval=0.95,
                geo_promo=False,
            )
            second_call = mock_print.call_args[0][0]

            # Both calls should produce identical output
            assert first_call == second_call

            # Parse and verify scores are identical
            import json

            first_result = json.loads(first_call)
            second_result = json.loads(second_call)

            assert first_result["score"] == second_result["score"]
            assert first_result["signals"] == second_result["signals"]

    def test_different_inputs_produce_different_scores(self):
        """Test that different inputs produce different scores."""
        from altwallet_merchant_agent.cli import _demo_logic

        with patch("altwallet_merchant_agent.cli.console.print") as mock_print:
            # First call
            _demo_logic(
                merchant="Whole Foods",
                amount=180.0,
                location="New York",
                json_output=True,
                verbose=False,
                p_approval=0.95,
                geo_promo=False,
            )
            first_call = mock_print.call_args[0][0]

            mock_print.reset_mock()

            # Second call with different amount
            _demo_logic(
                merchant="Whole Foods",
                amount=200.0,
                location="New York",
                json_output=True,
                verbose=False,
                p_approval=0.95,
                geo_promo=False,
            )
            second_call = mock_print.call_args[0][0]

            # Parse and verify scores are different
            import json

            first_result = json.loads(first_call)
            second_result = json.loads(second_call)

            assert first_result["score"] != second_result["score"]
            assert abs(first_result["score"] - 5.13) < 0.01  # 180 * 0.03 * 0.95
            assert abs(second_result["score"] - 5.7) < 0.01  # 200 * 0.03 * 0.95

    def test_demo_calculation_logic(self):
        """Test the demo calculation logic (3% base reward, 0 penalty, 0.95 p_approval)."""
        from altwallet_merchant_agent.cli import _demo_logic

        test_cases = [
            (100.0, 2.85),  # 100 * 0.03 * 0.95 = 2.85
            (200.0, 5.7),  # 200 * 0.03 * 0.95 = 5.7
            (50.0, 1.425),  # 50 * 0.03 * 0.95 = 1.425
            (0.0, 0.0),  # 0 * 0.03 * 0.95 = 0.0
        ]

        for amount, expected_score in test_cases:
            with patch("altwallet_merchant_agent.cli.console.print") as mock_print:
                _demo_logic(
                    merchant="Test Merchant",
                    amount=amount,
                    location="Test Location",
                    json_output=True,
                    verbose=False,
                    p_approval=0.95,
                    geo_promo=False,
                )

                import json

                result = json.loads(mock_print.call_args[0][0])

                assert abs(result["score"] - expected_score) < 0.01
                assert result["signals"]["rewards_value_usd"] == amount * 0.03
                assert result["signals"]["merchant_penalty_usd"] == 0.0

    def test_p_approval_enhancement(self):
        """Test the p_approval enhancement stub."""
        from altwallet_merchant_agent.cli import _demo_logic

        with patch("altwallet_merchant_agent.cli.console.print") as mock_print:
            # Test with p_approval = 0.8 (should multiply score by 0.8)
            _demo_logic(
                merchant="Test Merchant",
                amount=100.0,
                location="Test Location",
                json_output=True,
                verbose=False,
                p_approval=0.8,
            )

            import json

            result = json.loads(mock_print.call_args[0][0])

            # Base score should be 3.0 (100 * 0.03), multiplied by 0.8 = 2.4
            assert abs(result["score"] - 2.4) < 0.01
            assert result["signals"]["p_approval_used"] == 0.8

    def test_geo_promo_enhancement(self):
        """Test the geo_promo enhancement stub."""
        from altwallet_merchant_agent.cli import _demo_logic

        with patch("altwallet_merchant_agent.cli.console.print") as mock_print:
            # Test with geo_promo enabled
            _demo_logic(
                merchant="Test Merchant",
                amount=100.0,
                location="Test Location",
                json_output=True,
                verbose=False,
                geo_promo=True,
            )

            import json

            result = json.loads(mock_print.call_args[0][0])

            # Base rewards should be 3.0 (100 * 0.03), plus 1.50 geo promo = 4.50
            assert result["signals"]["rewards_value_usd"] == 4.5
            assert result["signals"]["geo_promo_applied"] is True
            # Score should be 4.5 * 0.95 (default p_approval) = 4.275
            assert abs(result["score"] - 4.275) < 0.01

    def test_p_approval_validation(self):
        """Test that p_approval validation works correctly."""
        from altwallet_merchant_agent.cli import _demo_logic

        with patch("altwallet_merchant_agent.cli.console.print") as mock_print:
            # Test with invalid p_approval value
            with pytest.raises(
                (SystemExit, click.exceptions.Exit)
            ):  # typer.Exit raises SystemExit
                _demo_logic(
                    merchant="Test Merchant",
                    amount=100.0,
                    location="Test Location",
                    json_output=True,
                    verbose=False,
                    p_approval=1.5,
                )  # Invalid: > 1

            # Verify error message was printed
            mock_print.assert_called()
            error_call = mock_print.call_args[0][0]
            assert "p_approval must be between 0 and 1" in error_call
