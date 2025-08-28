"""Composite Utility Module for AltWallet Checkout Agent.

This module calculates composite utility scores for card recommendations by combining:
- Approval probability (p_approval)
- Expected rewards
- Preference weight
- Merchant penalty

The utility score is used to rank cards in order of optimal choice for the user.
"""

from typing import Any

from .logger import get_logger
from .merchant_penalty import MerchantPenalty
from .models import Context
from .preference_weighting import PreferenceWeighting
from .scoring import score_transaction

logger = get_logger(__name__)


class CompositeUtility:
    """Calculates composite utility scores for card recommendations."""

    def __init__(self):
        """Initialize the composite utility calculator."""
        self.preference_weighting = PreferenceWeighting()
        self.merchant_penalty = MerchantPenalty()
        logger.info("Composite utility calculator initialized")

    def calculate_card_utility(
        self, card: dict[str, Any], context: Context
    ) -> dict[str, Any]:
        """Calculate composite utility for a single card.

        Args:
            card: Card information dictionary
            context: Transaction context

        Returns:
            Dictionary containing utility score and component breakdown
        """
        try:
            # Validate card has required fields
            if not isinstance(card, dict) or "name" not in card:
                raise ValueError("Invalid card format: missing required fields")

            # Calculate approval probability (p_approval)
            score_result = score_transaction(context)
            p_approval = self._score_to_approval_probability(score_result.final_score)

            # Calculate expected rewards
            expected_rewards = self._calculate_expected_rewards(card, context)

            # Calculate preference weight
            preference_weight = self.preference_weighting.preference_weight(
                card, context
            )

            # Calculate merchant penalty
            merchant_penalty = self.merchant_penalty.merchant_penalty(context)

            # Calculate composite utility
            utility = (
                p_approval * expected_rewards * preference_weight * merchant_penalty
            )

            # Create detailed breakdown
            utility_breakdown = {
                "card_id": card.get("card_id", "unknown"),
                "card_name": card.get("name", "Unknown Card"),
                "utility_score": utility,
                "components": {
                    "p_approval": p_approval,
                    "expected_rewards": expected_rewards,
                    "preference_weight": preference_weight,
                    "merchant_penalty": merchant_penalty,
                },
                "score_result": {
                    "risk_score": score_result.risk_score,
                    "loyalty_boost": score_result.loyalty_boost,
                    "final_score": score_result.final_score,
                    "routing_hint": score_result.routing_hint,
                },
                "context_info": {
                    "merchant_name": (
                        context.merchant.name if context.merchant else "Unknown"
                    ),
                    "merchant_mcc": (
                        context.merchant.mcc if context.merchant else "Unknown"
                    ),
                    "cart_total": float(context.cart.total) if context.cart else 0.0,
                    "loyalty_tier": context.customer.loyalty_tier.value,
                },
            }

            logger.debug(
                f"Card utility calculated for {card.get('name', 'Unknown')}",
                card_id=card.get("card_id"),
                utility_score=utility,
                p_approval=p_approval,
                expected_rewards=expected_rewards,
                preference_weight=preference_weight,
                merchant_penalty=merchant_penalty,
            )

            return utility_breakdown

        except Exception as e:
            logger.error(
                f"Error calculating utility for card {card.get('name', 'Unknown')}: {e}"
            )
            # Return default utility breakdown on error
            return {
                "card_id": card.get("card_id", "unknown"),
                "card_name": card.get("name", "Unknown Card"),
                "utility_score": 0.0,
                "components": {
                    "p_approval": 0.5,
                    "expected_rewards": 0.0,
                    "preference_weight": 1.0,
                    "merchant_penalty": 1.0,
                },
                "error": str(e),
            }

    def rank_cards_by_utility(
        self, cards: list[dict[str, Any]], context: Context
    ) -> list[dict[str, Any]]:
        """Rank cards by their composite utility scores.

        Args:
            cards: List of card dictionaries
            context: Transaction context

        Returns:
            List of cards ranked by utility score (highest first)
        """
        logger.info(f"Ranking {len(cards)} cards by utility")

        # Calculate utility for each card
        card_utilities = []
        for card in cards:
            utility_breakdown = self.calculate_card_utility(card, context)
            card_utilities.append(utility_breakdown)

        # Sort by utility score (descending)
        ranked_cards = sorted(
            card_utilities, key=lambda x: x["utility_score"], reverse=True
        )

        # Add ranking information
        for i, card in enumerate(ranked_cards):
            card["rank"] = i + 1
            card["rank_percentage"] = (len(ranked_cards) - i) / len(ranked_cards)

        logger.info(
            "Cards ranked by utility",
            top_card=ranked_cards[0]["card_name"] if ranked_cards else "None",
            top_utility=ranked_cards[0]["utility_score"] if ranked_cards else 0.0,
            total_cards=len(ranked_cards),
        )

        return ranked_cards

    def _score_to_approval_probability(self, score: int) -> float:
        """Convert scoring system score to approval probability.

        Args:
            score: Score from 0-120 (or higher with loyalty boost)

        Returns:
            Approval probability between 0.0 and 1.0
        """
        # Normalize score to 0-100 range first
        normalized_score = min(score, 120) / 120.0

        # Convert to probability using sigmoid-like function
        # Higher scores = higher approval probability
        if normalized_score >= 0.8:
            return 0.95  # Very high approval probability
        elif normalized_score >= 0.6:
            return 0.85  # High approval probability
        elif normalized_score >= 0.3:
            return 0.70  # Medium approval probability
        elif normalized_score >= 0.15:
            return 0.50  # Low approval probability
        else:
            return 0.25  # Very low approval probability

    def _calculate_expected_rewards(
        self, card: dict[str, Any], context: Context
    ) -> float:
        """Calculate expected rewards for a card given the transaction context.

        Args:
            card: Card information dictionary
            context: Transaction context

        Returns:
            Expected rewards as a multiplier (e.g., 1.05 = 5% rewards)
        """
        try:
            # Base rewards rate from card
            base_rate = card.get("cashback_rate", 0.01)  # Default 1%

            # Get transaction amount
            cart_total = float(context.cart.total) if context.cart else 0.0

            # Calculate base rewards
            base_rewards = base_rate * cart_total

            # Apply category bonuses if available
            category_bonus = self._get_category_bonus(card, context)
            category_rewards = base_rewards * category_bonus

            # Apply signup bonus if eligible
            signup_bonus = self._get_signup_bonus(card, context)

            # Calculate total expected rewards
            total_rewards = category_rewards + signup_bonus

            # Convert to multiplier (rewards per dollar spent)
            if cart_total > 0:
                rewards_multiplier = total_rewards / cart_total
            else:
                rewards_multiplier = base_rate

            # Cap at reasonable maximum (e.g., 10% total rewards)
            rewards_multiplier = min(rewards_multiplier, 0.10)

            return rewards_multiplier

        except Exception as e:
            logger.error(f"Error calculating expected rewards: {e}")
            return card.get("cashback_rate", 0.01)

    def _get_category_bonus(self, card: dict[str, Any], context: Context) -> float:
        """Get category bonus multiplier for the card.

        Args:
            card: Card information dictionary
            context: Transaction context

        Returns:
            Category bonus multiplier
        """
        # Get merchant MCC
        mcc = context.merchant.mcc if context.merchant else "default"

        # Get card category bonuses
        category_bonuses = card.get("category_bonuses", {})

        # Check for exact MCC match
        if mcc in category_bonuses:
            return category_bonuses[mcc]

        # Check for MCC family match (first 2 digits)
        if len(mcc) >= 2:
            mcc_family = mcc[:2]
            for bonus_mcc, bonus_rate in category_bonuses.items():
                if bonus_mcc.startswith(mcc_family):
                    return bonus_rate

        # Default bonus (no category bonus)
        return 1.0

    def _get_signup_bonus(self, card: dict[str, Any], context: Context) -> float:
        """Get signup bonus for the card if eligible.

        Args:
            card: Card information dictionary
            context: Transaction context

        Returns:
            Signup bonus amount
        """
        # Check if user is eligible for signup bonus
        # This would typically check against user's card history
        # For now, return 0 (no signup bonus)
        return 0.0

    def analyze_utility_components(
        self, cards: list[dict[str, Any]], context: Context
    ) -> dict[str, Any]:
        """Analyze utility components across all cards.

        Args:
            cards: List of card dictionaries
            context: Transaction context

        Returns:
            Analysis of utility components
        """
        ranked_cards = self.rank_cards_by_utility(cards, context)

        if not ranked_cards:
            return {"error": "No cards to analyze"}

        # Calculate component statistics
        p_approvals = [card["components"]["p_approval"] for card in ranked_cards]
        expected_rewards = [
            card["components"]["expected_rewards"] for card in ranked_cards
        ]
        preference_weights = [
            card["components"]["preference_weight"] for card in ranked_cards
        ]
        merchant_penalties = [
            card["components"]["merchant_penalty"] for card in ranked_cards
        ]
        utilities = [card["utility_score"] for card in ranked_cards]

        analysis = {
            "total_cards": len(ranked_cards),
            "top_card": ranked_cards[0]["card_name"],
            "top_utility": ranked_cards[0]["utility_score"],
            "utility_range": {
                "min": min(utilities),
                "max": max(utilities),
                "avg": sum(utilities) / len(utilities),
            },
            "component_ranges": {
                "p_approval": {"min": min(p_approvals), "max": max(p_approvals)},
                "expected_rewards": {
                    "min": min(expected_rewards),
                    "max": max(expected_rewards),
                },
                "preference_weight": {
                    "min": min(preference_weights),
                    "max": max(preference_weights),
                },
                "merchant_penalty": {
                    "min": min(merchant_penalties),
                    "max": max(merchant_penalties),
                },
            },
            "rankings": ranked_cards,
        }

        return analysis
