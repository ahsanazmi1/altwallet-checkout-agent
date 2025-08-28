"""Tests for Composite Utility Module."""

import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock

from altwallet_agent.composite_utility import CompositeUtility
from altwallet_agent.models import (
    Context,
    Customer,
    Merchant,
    Cart,
    CartItem,
    LoyaltyTier,
    Device,
    Geo,
)


class TestCompositeUtility:
    """Test cases for CompositeUtility class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.utility = CompositeUtility()

        # Sample cards for testing
        self.sample_cards = [
            {
                "card_id": "chase_sapphire_preferred",
                "name": "Chase Sapphire Preferred",
                "cashback_rate": 0.02,
                "category_bonuses": {
                    "4511": 2.0,  # Airlines
                    "5812": 2.0,  # Restaurants
                    "4722": 2.0,  # Travel agencies
                },
                "issuer": "chase",
                "annual_fee": 95,
                "rewards_type": "points",
            },
            {
                "card_id": "amex_gold",
                "name": "American Express Gold",
                "cashback_rate": 0.04,
                "category_bonuses": {
                    "5812": 4.0,  # Restaurants
                    "5411": 4.0,  # Grocery stores
                },
                "issuer": "american_express",
                "annual_fee": 250,
                "rewards_type": "points",
            },
            {
                "card_id": "chase_freedom_unlimited",
                "name": "Chase Freedom Unlimited",
                "cashback_rate": 0.015,
                "category_bonuses": {},
                "issuer": "chase",
                "annual_fee": 0,
                "rewards_type": "cashback",
            },
            {
                "card_id": "citi_double_cash",
                "name": "Citi Double Cash",
                "cashback_rate": 0.02,
                "category_bonuses": {},
                "issuer": "citi",
                "annual_fee": 0,
                "rewards_type": "cashback",
            },
        ]

    def create_sample_context(
        self,
        loyalty_tier: LoyaltyTier = LoyaltyTier.GOLD,
        mcc: str = "5411",
        merchant_name: str = "Sample Store",
        network_preferences: list = None,
    ) -> Context:
        """Create a sample context for testing."""
        if network_preferences is None:
            network_preferences = ["visa", "mastercard"]

        return Context(
            customer=Customer(
                id="test_customer",
                loyalty_tier=loyalty_tier,
                historical_velocity_24h=1,
                chargebacks_12m=0,
            ),
            merchant=Merchant(
                name=merchant_name,
                mcc=mcc,
                network_preferences=network_preferences,
                location={"city": "New York", "country": "US"},
            ),
            cart=Cart(
                items=[
                    CartItem(
                        item="Test Item",
                        unit_price=Decimal("100.00"),
                        qty=1,
                        mcc=mcc,
                        merchant_category="Test Category",
                    )
                ],
                currency="USD",
            ),
            device=Device(
                ip="192.168.1.1",
                device_id="test_device_123",
                ip_distance_km=5.0,
                location={"city": "New York", "country": "US"},
            ),
            geo=Geo(
                city="New York",
                region="NY",
                country="US",
                lat=40.7128,
                lon=-74.0060,
            ),
        )

    def test_init(self):
        """Test initialization of CompositeUtility."""
        utility = CompositeUtility()
        assert utility.preference_weighting is not None
        assert utility.merchant_penalty is not None

    @patch("altwallet_agent.composite_utility.score_transaction")
    def test_calculate_card_utility_basic(self, mock_score_transaction):
        """Test basic card utility calculation."""
        # Mock scoring result
        mock_score_result = MagicMock()
        mock_score_result.final_score = 85
        mock_score_result.risk_score = 20
        mock_score_result.loyalty_boost = 10
        mock_score_result.routing_hint = "visa"
        mock_score_transaction.return_value = mock_score_result

        # Mock preference and penalty calculations
        with patch.object(
            self.utility.preference_weighting, "preference_weight", return_value=1.1
        ):
            with patch.object(
                self.utility.merchant_penalty, "merchant_penalty", return_value=0.95
            ):
                context = self.create_sample_context()
                card = self.sample_cards[0]

                result = self.utility.calculate_card_utility(card, context)

                assert "utility_score" in result
                assert "components" in result
                assert "p_approval" in result["components"]
                assert "expected_rewards" in result["components"]
                assert "preference_weight" in result["components"]
                assert "merchant_penalty" in result["components"]
                assert result["utility_score"] > 0

    def test_rank_cards_by_utility(self):
        """Test ranking cards by utility score."""
        context = self.create_sample_context()

        # Mock all the component calculations
        with patch.object(self.utility, "calculate_card_utility") as mock_calc:
            # Create mock utility results for all 4 sample cards
            mock_results = [
                {
                    "card_id": "card1",
                    "card_name": "Card 1",
                    "utility_score": 0.85,
                    "components": {},
                },
                {
                    "card_id": "card2",
                    "card_name": "Card 2",
                    "utility_score": 0.92,
                    "components": {},
                },
                {
                    "card_id": "card3",
                    "card_name": "Card 3",
                    "utility_score": 0.78,
                    "components": {},
                },
                {
                    "card_id": "card4",
                    "card_name": "Card 4",
                    "utility_score": 0.65,
                    "components": {},
                },
            ]
            mock_calc.side_effect = mock_results

            ranked_cards = self.utility.rank_cards_by_utility(
                self.sample_cards, context
            )

            # Should be ranked by utility score (descending)
            assert ranked_cards[0]["utility_score"] == 0.92  # Card 2
            assert ranked_cards[1]["utility_score"] == 0.85  # Card 1
            assert ranked_cards[2]["utility_score"] == 0.78  # Card 3
            assert ranked_cards[3]["utility_score"] == 0.65  # Card 4

            # Should have rank information
            assert ranked_cards[0]["rank"] == 1
            assert ranked_cards[1]["rank"] == 2
            assert ranked_cards[2]["rank"] == 3
            assert ranked_cards[3]["rank"] == 4

    def test_score_to_approval_probability(self):
        """Test score to approval probability conversion."""
        # Test high scores
        assert self.utility._score_to_approval_probability(100) == 0.95
        assert self.utility._score_to_approval_probability(96) == 0.95  # 96/120 = 0.8
        assert self.utility._score_to_approval_probability(90) == 0.85  # 90/120 = 0.75

        # Test medium scores
        assert self.utility._score_to_approval_probability(72) == 0.85  # 72/120 = 0.6
        assert self.utility._score_to_approval_probability(70) == 0.70  # 70/120 = 0.583

        # Test low scores
        assert self.utility._score_to_approval_probability(40) == 0.70
        assert self.utility._score_to_approval_probability(20) == 0.50
        assert self.utility._score_to_approval_probability(10) == 0.25

    def test_calculate_expected_rewards(self):
        """Test expected rewards calculation."""
        context = self.create_sample_context()
        card = self.sample_cards[0]  # Chase Sapphire Preferred

        rewards = self.utility._calculate_expected_rewards(card, context)
        assert rewards > 0
        assert rewards <= 0.10  # Should be capped at 10%

    def test_get_category_bonus(self):
        """Test category bonus calculation."""
        context = self.create_sample_context(mcc="4511")  # Airlines
        card = self.sample_cards[0]  # Chase Sapphire Preferred (2x on airlines)

        bonus = self.utility._get_category_bonus(card, context)
        assert bonus == 2.0

        # Test with no category bonus
        context = self.create_sample_context(mcc="5311")  # Department stores
        bonus = self.utility._get_category_bonus(card, context)
        assert bonus == 1.0

    def test_analyze_utility_components(self):
        """Test utility component analysis."""
        context = self.create_sample_context()

        with patch.object(self.utility, "rank_cards_by_utility") as mock_rank:
            mock_rank.return_value = [
                {
                    "card_name": "Top Card",
                    "utility_score": 0.85,
                    "components": {
                        "p_approval": 0.9,
                        "expected_rewards": 0.03,
                        "preference_weight": 1.1,
                        "merchant_penalty": 0.95,
                    },
                },
                {
                    "card_name": "Second Card",
                    "utility_score": 0.75,
                    "components": {
                        "p_approval": 0.8,
                        "expected_rewards": 0.025,
                        "preference_weight": 1.0,
                        "merchant_penalty": 0.98,
                    },
                },
            ]

            analysis = self.utility.analyze_utility_components(
                self.sample_cards, context
            )

            assert analysis["total_cards"] == 2
            assert analysis["top_card"] == "Top Card"
            assert analysis["top_utility"] == 0.85
            assert "utility_range" in analysis
            assert "component_ranges" in analysis

    def test_travel_vs_grocery_rank_shifts(self):
        """Test rank shifts between travel and grocery MCCs."""
        # Create travel context (airlines)
        travel_context = self.create_sample_context(
            mcc="4511", merchant_name="Delta Airlines"
        )

        # Create grocery context
        grocery_context = self.create_sample_context(
            mcc="5411", merchant_name="Whole Foods"
        )

        with patch.object(self.utility, "calculate_card_utility") as mock_calc:
            # Mock utility results for travel
            travel_utilities = [
                {
                    "card_id": "chase_sapphire_preferred",
                    "card_name": "Chase Sapphire Preferred",
                    "utility_score": 0.92,  # High for travel (2x bonus)
                    "components": {},
                },
                {
                    "card_id": "amex_gold",
                    "card_name": "American Express Gold",
                    "utility_score": 0.78,  # Lower for travel
                    "components": {},
                },
            ]

            # Mock utility results for grocery
            grocery_utilities = [
                {
                    "card_id": "amex_gold",
                    "card_name": "American Express Gold",
                    "utility_score": 0.95,  # High for grocery (4x bonus)
                    "components": {},
                },
                {
                    "card_id": "chase_sapphire_preferred",
                    "card_name": "Chase Sapphire Preferred",
                    "utility_score": 0.82,  # Lower for grocery
                    "components": {},
                },
            ]

            mock_calc.side_effect = travel_utilities + grocery_utilities

            # Rank for travel
            travel_ranked = self.utility.rank_cards_by_utility(
                self.sample_cards[:2], travel_context
            )

            # Rank for grocery
            grocery_ranked = self.utility.rank_cards_by_utility(
                self.sample_cards[:2], grocery_context
            )

            # Verify rank shifts
            assert travel_ranked[0]["card_name"] == "Chase Sapphire Preferred"
            assert grocery_ranked[0]["card_name"] == "American Express Gold"

            # Chase should be better for travel, Amex better for grocery
            assert travel_ranked[0]["utility_score"] > travel_ranked[1]["utility_score"]
            assert (
                grocery_ranked[0]["utility_score"] > grocery_ranked[1]["utility_score"]
            )

    def test_loyalty_tier_rank_shifts(self):
        """Test rank shifts between different loyalty tiers."""
        # Create GOLD loyalty context
        gold_context = self.create_sample_context(loyalty_tier=LoyaltyTier.GOLD)

        # Create NONE loyalty context
        none_context = self.create_sample_context(loyalty_tier=LoyaltyTier.NONE)

        with patch.object(self.utility, "calculate_card_utility") as mock_calc:
            # Mock utility results for GOLD tier
            gold_utilities = [
                {
                    "card_id": "chase_sapphire_preferred",
                    "card_name": "Chase Sapphire Preferred",
                    "utility_score": 0.88,  # Higher for GOLD tier
                    "components": {},
                },
                {
                    "card_id": "chase_freedom_unlimited",
                    "card_name": "Chase Freedom Unlimited",
                    "utility_score": 0.82,
                    "components": {},
                },
            ]

            # Mock utility results for NONE tier
            none_utilities = [
                {
                    "card_id": "chase_freedom_unlimited",
                    "card_name": "Chase Freedom Unlimited",
                    "utility_score": 0.85,  # Better for NONE tier (no annual fee)
                    "components": {},
                },
                {
                    "card_id": "chase_sapphire_preferred",
                    "card_name": "Chase Sapphire Preferred",
                    "utility_score": 0.78,  # Lower for NONE tier (annual fee penalty)
                    "components": {},
                },
            ]

            mock_calc.side_effect = gold_utilities + none_utilities

            # Rank for GOLD tier
            gold_ranked = self.utility.rank_cards_by_utility(
                self.sample_cards[:2], gold_context
            )

            # Rank for NONE tier
            none_ranked = self.utility.rank_cards_by_utility(
                self.sample_cards[:2], none_context
            )

            # Verify rank shifts
            assert gold_ranked[0]["card_name"] == "Chase Sapphire Preferred"
            assert none_ranked[0]["card_name"] == "Chase Freedom Unlimited"

            # Premium cards should be better for higher loyalty tiers
            assert gold_ranked[0]["utility_score"] > gold_ranked[1]["utility_score"]
            assert none_ranked[0]["utility_score"] > none_ranked[1]["utility_score"]

    def test_merchant_debit_preference_rank_shifts(self):
        """Test rank shifts when merchant prefers debit."""
        # Create context with debit preference
        debit_context = self.create_sample_context(
            network_preferences=["debit"], merchant_name="Gas Station"
        )

        # Create context with no preference
        no_pref_context = self.create_sample_context(
            network_preferences=[], merchant_name="Online Store"
        )

        with patch.object(self.utility, "calculate_card_utility") as mock_calc:
            # Mock utility results for debit preference
            debit_utilities = [
                {
                    "card_id": "chase_freedom_unlimited",
                    "card_name": "Chase Freedom Unlimited",
                    "utility_score": 0.82,  # Better with debit preference (lower penalty)
                    "components": {},
                },
                {
                    "card_id": "amex_gold",
                    "card_name": "American Express Gold",
                    "utility_score": 0.75,  # Worse with debit preference (higher penalty)
                    "components": {},
                },
            ]

            # Mock utility results for no preference
            no_pref_utilities = [
                {
                    "card_id": "amex_gold",
                    "card_name": "American Express Gold",
                    "utility_score": 0.88,  # Better with no preference
                    "components": {},
                },
                {
                    "card_id": "chase_freedom_unlimited",
                    "card_name": "Chase Freedom Unlimited",
                    "utility_score": 0.85,
                    "components": {},
                },
            ]

            mock_calc.side_effect = debit_utilities + no_pref_utilities

            # Rank for debit preference
            debit_ranked = self.utility.rank_cards_by_utility(
                self.sample_cards[:2], debit_context
            )

            # Rank for no preference
            no_pref_ranked = self.utility.rank_cards_by_utility(
                self.sample_cards[:2], no_pref_context
            )

            # Verify rank shifts
            assert debit_ranked[0]["card_name"] == "Chase Freedom Unlimited"
            assert no_pref_ranked[0]["card_name"] == "American Express Gold"

            # Debit-friendly cards should be better when merchant prefers debit
            assert debit_ranked[0]["utility_score"] > debit_ranked[1]["utility_score"]
            assert (
                no_pref_ranked[0]["utility_score"] > no_pref_ranked[1]["utility_score"]
            )

    def test_error_handling(self):
        """Test error handling in utility calculation."""
        context = self.create_sample_context()
        invalid_card = {"invalid": "card"}

        result = self.utility.calculate_card_utility(invalid_card, context)

        assert "error" in result
        assert result["utility_score"] == 0.0
        assert result["components"]["p_approval"] == 0.5
        assert result["components"]["expected_rewards"] == 0.0

    def test_empty_cards_list(self):
        """Test handling of empty cards list."""
        context = self.create_sample_context()

        ranked_cards = self.utility.rank_cards_by_utility([], context)
        assert ranked_cards == []

        analysis = self.utility.analyze_utility_components([], context)
        assert "error" in analysis
