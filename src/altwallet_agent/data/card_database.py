"""Card database and metadata for AltWallet Checkout Agent.

This module provides a comprehensive database of credit cards with their
rewards structures, annual fees, and category bonuses for intelligent
recommendations.
"""

from typing import Any


class CardDatabase:
    """Database of credit cards with rewards and metadata.

    This database contains comprehensive information about various credit cards
    including their rewards structures, annual fees, category bonuses, and
    eligibility requirements for intelligent recommendation algorithms.

    Attributes:
        cards: Dictionary mapping card IDs to card metadata
        categories: Dictionary of merchant categories and their codes
    """

    def __init__(self) -> None:
        """Initialize the card database with comprehensive card data."""
        self.cards = self._initialize_cards()
        self.categories = self._initialize_categories()

    def _initialize_cards(self) -> dict[str, dict[str, Any]]:
        """Initialize the comprehensive card database.

        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of card metadata
        """
        return {
            "chase_sapphire_preferred": {
                "name": "Chase Sapphire Preferred",
                "issuer": "Chase",
                "annual_fee": 95,
                "base_rewards_rate": 0.02,
                "signup_bonus_points": 60000,
                "signup_bonus_value": 750,
                "category_bonuses": {
                    "travel": 0.025,
                    "dining": 0.025,
                    "online_grocery": 0.025,
                },
                "travel_benefits": ["Trip cancellation insurance", "Auto rental CDW"],
                "foreign_transaction_fee": 0.0,
                "credit_score_required": "Good",
                "intro_apr": 0.0,
                "intro_period_months": 15,
            },
            "chase_sapphire_reserve": {
                "name": "Chase Sapphire Reserve",
                "issuer": "Chase",
                "annual_fee": 550,
                "base_rewards_rate": 0.03,
                "signup_bonus_points": 60000,
                "signup_bonus_value": 900,
                "category_bonuses": {
                    "travel": 0.03,
                    "dining": 0.03,
                },
                "travel_benefits": [
                    "Priority Pass lounge access",
                    "Global Entry credit",
                    "Trip cancellation insurance",
                ],
                "foreign_transaction_fee": 0.0,
                "credit_score_required": "Excellent",
                "intro_apr": 0.0,
                "intro_period_months": 15,
            },
            "amex_gold": {
                "name": "American Express Gold",
                "issuer": "American Express",
                "annual_fee": 250,
                "base_rewards_rate": 0.01,
                "signup_bonus_points": 60000,
                "signup_bonus_value": 1200,
                "category_bonuses": {
                    "dining": 0.04,
                    "grocery_stores": 0.04,
                    "airfare": 0.03,
                },
                "travel_benefits": ["Flight credit", "Hotel credit"],
                "foreign_transaction_fee": 0.0275,
                "credit_score_required": "Good",
                "intro_apr": 0.0,
                "intro_period_months": 12,
            },
            "amex_platinum": {
                "name": "American Express Platinum",
                "issuer": "American Express",
                "annual_fee": 695,
                "base_rewards_rate": 0.01,
                "signup_bonus_points": 80000,
                "signup_bonus_value": 1600,
                "category_bonuses": {
                    "airfare": 0.05,
                    "prepaid_hotels": 0.05,
                },
                "travel_benefits": [
                    "Centurion lounge access",
                    "Priority Pass lounge access",
                    "Global Entry credit",
                    "Hotel elite status",
                ],
                "foreign_transaction_fee": 0.0,
                "credit_score_required": "Excellent",
                "intro_apr": 0.0,
                "intro_period_months": 12,
            },
            "amazon_rewards_visa": {
                "name": "Amazon Rewards Visa",
                "issuer": "Chase",
                "annual_fee": 0,
                "base_rewards_rate": 0.01,
                "signup_bonus_points": 50000,
                "signup_bonus_value": 500,
                "category_bonuses": {
                    "amazon": 0.05,
                    "gas_stations": 0.02,
                    "restaurants": 0.02,
                    "drugstores": 0.02,
                },
                "travel_benefits": [],
                "foreign_transaction_fee": 0.03,
                "credit_score_required": "Fair",
                "intro_apr": 0.0,
                "intro_period_months": 6,
            },
            "citi_double_cash": {
                "name": "Citi Double Cash",
                "issuer": "Citi",
                "annual_fee": 0,
                "base_rewards_rate": 0.02,
                "signup_bonus_points": 0,
                "signup_bonus_value": 0,
                "category_bonuses": {},
                "travel_benefits": [],
                "foreign_transaction_fee": 0.03,
                "credit_score_required": "Good",
                "intro_apr": 0.0,
                "intro_period_months": 18,
            },
            "citi_custom_cash": {
                "name": "Citi Custom Cash",
                "issuer": "Citi",
                "annual_fee": 0,
                "base_rewards_rate": 0.01,
                "signup_bonus_points": 20000,
                "signup_bonus_value": 200,
                "category_bonuses": {
                    "top_spending_category": 0.05,
                },
                "travel_benefits": [],
                "foreign_transaction_fee": 0.03,
                "credit_score_required": "Good",
                "intro_apr": 0.0,
                "intro_period_months": 15,
            },
        }

    def _initialize_categories(self) -> dict[str, dict[str, Any]]:
        """Initialize merchant categories for classification.

        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of merchant categories
        """
        return {
            "travel": {
                "description": "Travel-related purchases",
                "subcategories": ["airfare", "hotels", "car_rental"],
            },
            "dining": {
                "description": "Restaurants and dining",
                "subcategories": ["restaurants", "fast_food", "bars"],
            },
            "grocery_stores": {
                "description": "Grocery store purchases",
                "subcategories": ["supermarkets", "grocery_stores"],
            },
            "gas_stations": {
                "description": "Gas station purchases",
                "subcategories": ["gas_stations", "fuel"],
            },
            "online_shopping": {
                "description": "Online retail purchases",
                "subcategories": ["amazon", "online_retail"],
            },
            "drugstores": {
                "description": "Drugstore purchases",
                "subcategories": ["pharmacies", "drugstores"],
            },
            "utilities": {
                "description": "Utility payments",
                "subcategories": ["electric", "water", "internet"],
            },
        }

    def get_card(self, card_id: str) -> dict[str, Any] | None:
        """Get card information by ID.

        Args:
            card_id: Unique identifier for the card

        Returns:
            Optional[Dict[str, Any]]: Card metadata or None if not found
        """
        return self.cards.get(card_id)

    def get_all_cards(self) -> dict[str, dict[str, Any]]:
        """Get all cards in the database.

        Returns:
            Dict[str, Dict[str, Any]]: All card metadata
        """
        return self.cards.copy()

    def get_cards_by_issuer(self, issuer: str) -> list[str]:
        """Get card IDs by issuer.

        Args:
            issuer: Card issuer name (e.g., 'Chase', 'American Express')

        Returns:
            List[str]: List of card IDs for the specified issuer
        """
        return [
            card_id
            for card_id, card_data in self.cards.items()
            if card_data["issuer"] == issuer
        ]

    def get_cards_by_annual_fee(self, max_fee: int) -> list[str]:
        """Get card IDs with annual fee less than or equal to specified amount.

        Args:
            max_fee: Maximum annual fee in dollars

        Returns:
            List[str]: List of card IDs meeting the criteria
        """
        return [
            card_id
            for card_id, card_data in self.cards.items()
            if card_data["annual_fee"] <= max_fee
        ]

    def get_cards_with_category_bonus(self, category: str) -> list[str]:
        """Get card IDs that offer bonuses for a specific category.

        Args:
            category: Merchant category (e.g., 'travel', 'dining')

        Returns:
            List[str]: List of card IDs offering category bonuses
        """
        return [
            card_id
            for card_id, card_data in self.cards.items()
            if category in card_data.get("category_bonuses", {})
        ]

    def calculate_effective_reward_rate(
        self, card_id: str, category: str | None = None
    ) -> float:
        """Calculate effective reward rate for a card in a category.

        Args:
            card_id: Unique identifier for the card
            category: Optional merchant category for bonus calculation

        Returns:
            float: Effective reward rate as a decimal
        """
        card_data = self.get_card(card_id)
        if not card_data:
            return 0.0

        base_rate = card_data["base_rewards_rate"]

        if category and category in card_data.get("category_bonuses", {}):
            bonus_rate = card_data["category_bonuses"][category]
            if isinstance(bonus_rate, (int, float)):
                return float(bonus_rate)

        return float(base_rate)

    def get_category_info(self, category: str) -> dict[str, Any] | None:
        """Get category information by name.

        Args:
            category: Category name

        Returns:
            Optional[Dict[str, Any]]: Category information or None if not found
        """
        return self.categories.get(category)

    def get_all_categories(self) -> dict[str, dict[str, Any]]:
        """Get all merchant categories.

        Returns:
            Dict[str, Dict[str, Any]]: All category information
        """
        return self.categories.copy()

    def search_cards(
        self,
        min_reward_rate: float | None = None,
        max_annual_fee: int | None = None,
        issuers: list[str] | None = None,
        categories: list[str] | None = None,
    ) -> list[str]:
        """Search for cards matching specific criteria.

        Args:
            min_reward_rate: Minimum base reward rate required
            max_annual_fee: Maximum annual fee allowed
            issuers: List of acceptable issuers
            categories: List of categories that should offer bonuses

        Returns:
            List[str]: List of card IDs matching the criteria
        """
        matching_cards = []

        for card_id, card_data in self.cards.items():
            # Check minimum reward rate
            if min_reward_rate and card_data["base_rewards_rate"] < min_reward_rate:
                continue

            # Check maximum annual fee
            if max_annual_fee and card_data["annual_fee"] > max_annual_fee:
                continue

            # Check issuers
            if issuers and card_data["issuer"] not in issuers:
                continue

            # Check categories
            if categories:
                card_categories = set(card_data.get("category_bonuses", {}).keys())
                if not card_categories.intersection(set(categories)):
                    continue

            matching_cards.append(card_id)

        return matching_cards


def get_card_database() -> list[dict[str, Any]]:
    """Get the card database as a list of card dictionaries.

    Returns:
        List[Dict[str, Any]]: List of card dictionaries with metadata
    """
    db = CardDatabase()
    cards = []
    for card_id, card_data in db.cards.items():
        card_dict = card_data.copy()
        card_dict["id"] = card_id
        cards.append(card_dict)
    return cards
