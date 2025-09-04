"""Preference & Loyalty Weighting Module for AltWallet Checkout Agent.

This module calculates preference-based weights for card recommendations by
considering user preferences, loyalty tiers, category boosts, and issuer
promotions. The weights are multiplicative factors in the range [0.5, 1.5]
centered at 1.0.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from .logger import get_logger
from .models import Context

logger = get_logger(__name__)


class PreferenceWeighting:
    """Calculates preference-based weights for card recommendations."""

    def __init__(self, config_path: str | None = None):
        """Initialize the preference weighting module.

        Args:
            config_path: Path to preferences configuration file
        """
        self.config = self._load_config(config_path)
        logger.info("Preference weighting module initialized")

    def _load_config(self, config_path: str | None = None) -> dict[str, Any]:
        """Load preferences configuration from YAML file.

        Args:
            config_path: Path to configuration file

        Returns:
            Configuration dictionary
        """
        if config_path is None:
            config_path = str(
                Path(__file__).parent.parent.parent / "config" / "preferences.yaml"
            )

        try:
            with open(config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded preferences config from {config_path}")
            if isinstance(config, dict):
                return config
            return self._get_default_config()
        except FileNotFoundError:
            logger.warning(
                f"Preferences config not found at {config_path}, using defaults"
            )
            return self._get_default_config()
        except yaml.YAMLError as e:
            logger.error(f"Error parsing preferences config: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> dict[str, Any]:
        """Get default configuration when config file is not available."""
        return {
            "user_preferences": {
                "cashback_vs_points_weight": 0.5,
                "issuer_affinity": {
                    "chase": 0.0,
                    "american_express": 0.0,
                    "citi": 0.0,
                    "capital_one": 0.0,
                    "wells_fargo": 0.0,
                    "bank_of_america": 0.0,
                    "discover": 0.0,
                    "us_bank": 0.0,
                },
                "annual_fee_tolerance": 0.5,
                "foreign_fee_sensitivity": 0.7,
            },
            "loyalty_tiers": {
                "NONE": 1.0,
                "SILVER": 1.05,
                "GOLD": 1.10,
                "PLATINUM": 1.15,
                "DIAMOND": 1.20,
            },
            "category_boosts": {
                "4511": 1.15,  # Airlines
                "5812": 1.10,  # Restaurants
                "5411": 1.08,  # Grocery stores
                "default": 1.0,
            },
            "calculation": {
                "min_weight": 0.5,
                "max_weight": 1.5,
                "base_weight": 1.0,
            },
        }

    def preference_weight(self, card: dict[str, Any], context: Context) -> float:
        """Calculate preference weight for a card given transaction context.

        Args:
            card: Card metadata dictionary
            context: Transaction context

        Returns:
            Multiplicative weight in range [0.5, 1.5]
        """
        try:
            # Calculate individual weight components
            user_pref_weight = self._calculate_user_preference_weight(card, context)
            loyalty_weight = self._calculate_loyalty_weight(context)
            category_weight = self._calculate_category_weight(card, context)
            promotion_weight = self._calculate_promotion_weight(card, context)

            # Combine weights using weighted average
            base_weight = self.config["calculation"]["base_weight"]
            if isinstance(base_weight, (int, float)):
                base_weight = float(base_weight)
            else:
                base_weight = 1.0

            final_weight = (
                user_pref_weight * 0.3
                + loyalty_weight * 0.2
                + category_weight * 0.25
                + promotion_weight * 0.15
                + base_weight * 0.1
            )

            # Apply bounds
            min_weight = self.config["calculation"]["min_weight"]
            max_weight = self.config["calculation"]["max_weight"]
            if isinstance(min_weight, (int, float)) and isinstance(
                max_weight, (int, float)
            ):
                final_weight = max(
                    float(min_weight), min(float(max_weight), final_weight)
                )

            logger.debug(
                f"Card {card.get('name', 'unknown')}: "
                f"user_pref={user_pref_weight:.3f}, "
                f"loyalty={loyalty_weight:.3f}, "
                f"category={category_weight:.3f}, "
                f"promotion={promotion_weight:.3f}, "
                f"final={final_weight:.3f}"
            )

            return float(final_weight)

        except Exception as e:
            logger.error(f"Error calculating preference weight: {e}")
            base_weight = self.config["calculation"]["base_weight"]
            if isinstance(base_weight, (int, float)):
                return float(base_weight)
            return 1.0

    def _calculate_user_preference_weight(
        self, card: dict[str, Any], context: Context
    ) -> float:
        """Calculate weight based on user preferences."""
        weight = 1.0

        # Cashback vs points preference
        cashback_vs_points = self.config["user_preferences"][
            "cashback_vs_points_weight"
        ]
        if isinstance(cashback_vs_points, (int, float)):
            cashback_vs_points = float(cashback_vs_points)
        else:
            cashback_vs_points = 0.5
        if "rewards_type" in card:
            if card["rewards_type"] == "cashback" and cashback_vs_points > 0.5:
                weight += 0.1
            elif card["rewards_type"] == "points" and cashback_vs_points < 0.5:
                weight += 0.1

        # Issuer affinity
        issuer = card.get("issuer", "").lower()
        issuer_affinity = self.config["user_preferences"]["issuer_affinity"].get(
            issuer, 0.0
        )
        if isinstance(issuer_affinity, (int, float)):
            weight += float(issuer_affinity)

        # Annual fee tolerance
        annual_fee = card.get("annual_fee", 0)
        fee_tolerance = self.config["user_preferences"]["annual_fee_tolerance"]
        if isinstance(fee_tolerance, (int, float)):
            fee_tolerance = float(fee_tolerance)
        else:
            fee_tolerance = 0.5
        if annual_fee > 0:
            if fee_tolerance < 0.3:  # Fee-averse
                weight -= 0.15
            elif fee_tolerance > 0.7:  # Fee-agnostic
                weight += 0.05

        # Foreign transaction fee sensitivity
        foreign_fee = card.get("foreign_transaction_fee", 0)
        fee_sensitivity = self.config["user_preferences"]["foreign_fee_sensitivity"]
        if isinstance(fee_sensitivity, (int, float)):
            fee_sensitivity = float(fee_sensitivity)
        else:
            fee_sensitivity = 0.7
        if foreign_fee > 0 and fee_sensitivity < 0.5:
            weight -= 0.1

        return weight

    def _calculate_loyalty_weight(self, context: Context) -> float:
        """Calculate weight based on customer loyalty tier."""
        loyalty_tier = context.customer.loyalty_tier
        loyalty_weight = self.config["loyalty_tiers"].get(loyalty_tier.value, 1.0)
        if isinstance(loyalty_weight, (int, float)):
            return float(loyalty_weight)
        return 1.0

    def _calculate_category_weight(
        self, card: dict[str, Any], context: Context
    ) -> float:
        """Calculate weight based on merchant category boosts."""
        # Get MCC from context
        mcc = None
        if context.merchant and context.merchant.mcc:
            mcc = context.merchant.mcc
        elif context.cart.items:
            # Use first item's MCC if available
            for item in context.cart.items:
                if item.mcc:
                    mcc = item.mcc
                    break

        if not mcc:
            default_boost = self.config["category_boosts"].get("default", 1.0)
            if isinstance(default_boost, (int, float)):
                return float(default_boost)
            return 1.0

        # Check if card has category bonuses that match the MCC
        category_bonuses = card.get("category_bonuses", {})
        if category_bonuses:
            # Simple MCC to category mapping
            mcc_to_category = {
                "4511": "travel",  # Airlines
                "4722": "travel",  # Travel agencies
                "5812": "dining",  # Restaurants
                "5813": "dining",  # Drinking places
                "5814": "dining",  # Fast food
                "5411": "grocery_stores",  # Grocery stores
                "5541": "gas_stations",  # Gas stations
                "5542": "gas_stations",  # Automated fuel
            }

            category = mcc_to_category.get(mcc)
            if category and category in category_bonuses:
                # Boost for cards with relevant category bonuses
                boost = self.config["category_boosts"].get(mcc, 1.0)
                if isinstance(boost, (int, float)):
                    return float(boost) * 1.05
                return 1.05

        # Return category boost if available, otherwise default
        boost = self.config["category_boosts"].get(mcc, 1.0)
        if isinstance(boost, (int, float)):
            return float(boost)
        return 1.0

    def _calculate_promotion_weight(
        self, card: dict[str, Any], context: Context
    ) -> float:
        """Calculate weight based on issuer promotions and credits."""
        weight = 1.0

        # Check for signup bonus
        if card.get("signup_bonus_points", 0) > 0:
            weight += 0.1

        # Check for travel benefits
        travel_benefits = card.get("travel_benefits", [])
        if travel_benefits:
            weight += 0.05

        # Check for seasonal promotions
        current_date = datetime.now()
        seasonal_promotions = self.config.get("seasonal_promotions", {})

        for _promotion_name, promotion_data in seasonal_promotions.items():
            if self._is_promotion_active(promotion_data, current_date):
                affected_categories = promotion_data.get("affected_categories", [])
                if self._is_category_affected(affected_categories, context):
                    multiplier = promotion_data.get("multiplier", 1.0)
                    if isinstance(multiplier, (int, float)):
                        weight *= float(multiplier)

        return weight

    def _is_promotion_active(
        self, promotion_data: dict[str, Any], current_date: datetime
    ) -> bool:
        """Check if a seasonal promotion is currently active."""
        try:
            start_date_str = promotion_data.get("start_date", "")
            end_date_str = promotion_data.get("end_date", "")

            if not start_date_str or not end_date_str:
                return False

            # Parse dates (assuming MM-DD format)
            start_month, start_day = map(int, start_date_str.split("-"))
            end_month, end_day = map(int, end_date_str.split("-"))

            current_month = current_date.month
            current_day = current_date.day

            # Handle year wrap-around (e.g., holiday season)
            if start_month > end_month:  # Crosses year boundary
                if (
                    current_month > start_month
                    or (current_month == start_month and current_day >= start_day)
                    or current_month < end_month
                    or (current_month == end_month and current_day <= end_day)
                ):
                    return True
            else:  # Within same year
                if (
                    current_month > start_month
                    or (current_month == start_month and current_day >= start_day)
                ) and (
                    current_month < end_month
                    or (current_month == end_month and current_day <= end_day)
                ):
                    return True

            return False

        except (ValueError, KeyError) as e:
            logger.warning(f"Error parsing promotion dates: {e}")
            return False

    def _is_category_affected(
        self, affected_categories: list, context: Context
    ) -> bool:
        """Check if the transaction category is affected by a promotion."""
        # Get MCC from context
        mcc = None
        if context.merchant and context.merchant.mcc:
            mcc = context.merchant.mcc
        elif context.cart.items:
            for item in context.cart.items:
                if item.mcc:
                    mcc = item.mcc
                    break

        return mcc in affected_categories if mcc else False
