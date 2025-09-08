"""Comprehensive tests for the card database module."""

import pytest

from altwallet_agent.data.card_database import CardDatabase, get_card_database


class TestCardDatabaseInitialization:
    """Test CardDatabase initialization and data loading."""

    def test_init_creates_database(self):
        """Test that initialization creates the database with cards and categories."""
        db = CardDatabase()

        assert isinstance(db.cards, dict)
        assert isinstance(db.categories, dict)
        assert len(db.cards) > 0
        assert len(db.categories) > 0

    def test_cards_contain_expected_data(self):
        """Test that cards contain all expected fields."""
        db = CardDatabase()

        # Check a specific card has all required fields
        chase_sapphire = db.cards.get("chase_sapphire_preferred")
        assert chase_sapphire is not None

        required_fields = [
            "name",
            "issuer",
            "annual_fee",
            "base_rewards_rate",
            "signup_bonus_points",
            "signup_bonus_value",
            "category_bonuses",
            "travel_benefits",
            "foreign_transaction_fee",
            "credit_score_required",
            "intro_apr",
            "intro_period_months",
        ]

        for field in required_fields:
            assert field in chase_sapphire

    def test_categories_contain_expected_data(self):
        """Test that categories contain all expected fields."""
        db = CardDatabase()

        # Check a specific category has all required fields
        travel_category = db.categories.get("travel")
        assert travel_category is not None

        required_fields = ["description", "subcategories"]
        for field in required_fields:
            assert field in travel_category

    def test_specific_cards_exist(self):
        """Test that specific expected cards exist in the database."""
        db = CardDatabase()

        expected_cards = [
            "chase_sapphire_preferred",
            "chase_sapphire_reserve",
            "amex_gold",
            "amex_platinum",
            "amazon_rewards_visa",
            "citi_double_cash",
            "citi_custom_cash",
        ]

        for card_id in expected_cards:
            assert card_id in db.cards

    def test_specific_categories_exist(self):
        """Test that specific expected categories exist in the database."""
        db = CardDatabase()

        expected_categories = [
            "travel",
            "dining",
            "grocery_stores",
            "gas_stations",
            "online_shopping",
            "drugstores",
            "utilities",
        ]

        for category in expected_categories:
            assert category in db.categories


class TestCardDatabaseCardRetrieval:
    """Test card retrieval methods."""

    def test_get_card_existing(self):
        """Test getting an existing card."""
        db = CardDatabase()

        card = db.get_card("chase_sapphire_preferred")
        assert card is not None
        assert card["name"] == "Chase Sapphire Preferred"
        assert card["issuer"] == "Chase"

    def test_get_card_nonexistent(self):
        """Test getting a non-existent card."""
        db = CardDatabase()

        card = db.get_card("nonexistent_card")
        assert card is None

    def test_get_card_empty_string(self):
        """Test getting a card with empty string ID."""
        db = CardDatabase()

        card = db.get_card("")
        assert card is None

    def test_get_all_cards(self):
        """Test getting all cards."""
        db = CardDatabase()

        all_cards = db.get_all_cards()
        assert isinstance(all_cards, dict)
        assert len(all_cards) > 0
        assert all_cards is not db.cards  # Should be a copy

    def test_get_cards_by_issuer_existing(self):
        """Test getting cards by existing issuer."""
        db = CardDatabase()

        chase_cards = db.get_cards_by_issuer("Chase")
        assert isinstance(chase_cards, list)
        assert len(chase_cards) > 0
        assert "chase_sapphire_preferred" in chase_cards
        assert "chase_sapphire_reserve" in chase_cards

    def test_get_cards_by_issuer_nonexistent(self):
        """Test getting cards by non-existent issuer."""
        db = CardDatabase()

        cards = db.get_cards_by_issuer("Nonexistent Bank")
        assert isinstance(cards, list)
        assert len(cards) == 0

    def test_get_cards_by_issuer_case_sensitive(self):
        """Test that issuer matching is case sensitive."""
        db = CardDatabase()

        chase_cards = db.get_cards_by_issuer("chase")  # lowercase
        assert len(chase_cards) == 0

    def test_get_cards_by_annual_fee_zero(self):
        """Test getting cards with zero annual fee."""
        db = CardDatabase()

        no_fee_cards = db.get_cards_by_annual_fee(0)
        assert isinstance(no_fee_cards, list)
        assert "amazon_rewards_visa" in no_fee_cards
        assert "citi_double_cash" in no_fee_cards

    def test_get_cards_by_annual_fee_high(self):
        """Test getting cards with high annual fee limit."""
        db = CardDatabase()

        all_cards = db.get_cards_by_annual_fee(1000)
        assert isinstance(all_cards, list)
        assert len(all_cards) > 0

    def test_get_cards_by_annual_fee_low(self):
        """Test getting cards with low annual fee limit."""
        db = CardDatabase()

        low_fee_cards = db.get_cards_by_annual_fee(100)
        assert isinstance(low_fee_cards, list)
        # Should include cards with fees <= 100
        for card_id in low_fee_cards:
            card = db.get_card(card_id)
            assert card["annual_fee"] <= 100

    def test_get_cards_with_category_bonus_existing(self):
        """Test getting cards with existing category bonus."""
        db = CardDatabase()

        travel_cards = db.get_cards_with_category_bonus("travel")
        assert isinstance(travel_cards, list)
        assert len(travel_cards) > 0

    def test_get_cards_with_category_bonus_nonexistent(self):
        """Test getting cards with non-existent category bonus."""
        db = CardDatabase()

        cards = db.get_cards_with_category_bonus("nonexistent_category")
        assert isinstance(cards, list)
        assert len(cards) == 0

    def test_get_cards_with_category_bonus_empty_string(self):
        """Test getting cards with empty category string."""
        db = CardDatabase()

        cards = db.get_cards_with_category_bonus("")
        assert isinstance(cards, list)
        assert len(cards) == 0


class TestCardDatabaseRewardCalculation:
    """Test reward rate calculation methods."""

    def test_calculate_effective_reward_rate_existing_card(self):
        """Test calculating effective reward rate for existing card."""
        db = CardDatabase()

        rate = db.calculate_effective_reward_rate("chase_sapphire_preferred")
        assert isinstance(rate, float)
        assert rate > 0

    def test_calculate_effective_reward_rate_with_category_bonus(self):
        """Test calculating effective reward rate with category bonus."""
        db = CardDatabase()

        rate = db.calculate_effective_reward_rate("chase_sapphire_preferred", "travel")
        assert isinstance(rate, float)
        assert rate > 0

    def test_calculate_effective_reward_rate_nonexistent_card(self):
        """Test calculating effective reward rate for non-existent card."""
        db = CardDatabase()

        rate = db.calculate_effective_reward_rate("nonexistent_card")
        assert rate == 0.0

    def test_calculate_effective_reward_rate_nonexistent_category(self):
        """Test calculating effective reward rate with non-existent category."""
        db = CardDatabase()

        rate = db.calculate_effective_reward_rate(
            "chase_sapphire_preferred", "nonexistent_category"
        )
        # Should return base rate since category doesn't exist
        base_rate = db.get_card("chase_sapphire_preferred")["base_rewards_rate"]
        assert rate == float(base_rate)

    def test_calculate_effective_reward_rate_empty_strings(self):
        """Test calculating effective reward rate with empty strings."""
        db = CardDatabase()

        rate = db.calculate_effective_reward_rate("", "")
        assert rate == 0.0

    def test_calculate_effective_reward_rate_returns_float(self):
        """Test that reward rate calculation always returns float."""
        db = CardDatabase()

        # Test with various card/category combinations
        test_cases = [
            ("chase_sapphire_preferred", None),
            ("chase_sapphire_preferred", "travel"),
            ("amex_gold", "dining"),
            ("citi_double_cash", None),
        ]

        for card_id, category in test_cases:
            rate = db.calculate_effective_reward_rate(card_id, category)
            assert isinstance(rate, float)


class TestCardDatabaseCategoryMethods:
    """Test category-related methods."""

    def test_get_category_info_existing(self):
        """Test getting existing category info."""
        db = CardDatabase()

        travel_info = db.get_category_info("travel")
        assert travel_info is not None
        assert "description" in travel_info
        assert "subcategories" in travel_info

    def test_get_category_info_nonexistent(self):
        """Test getting non-existent category info."""
        db = CardDatabase()

        info = db.get_category_info("nonexistent_category")
        assert info is None

    def test_get_category_info_empty_string(self):
        """Test getting category info with empty string."""
        db = CardDatabase()

        info = db.get_category_info("")
        assert info is None

    def test_get_all_categories(self):
        """Test getting all categories."""
        db = CardDatabase()

        all_categories = db.get_all_categories()
        assert isinstance(all_categories, dict)
        assert len(all_categories) > 0
        assert all_categories is not db.categories  # Should be a copy


class TestCardDatabaseSearch:
    """Test card search functionality."""

    def test_search_cards_no_criteria(self):
        """Test searching cards with no criteria."""
        db = CardDatabase()

        results = db.search_cards()
        assert isinstance(results, list)
        assert len(results) > 0

    def test_search_cards_min_reward_rate(self):
        """Test searching cards by minimum reward rate."""
        db = CardDatabase()

        results = db.search_cards(min_reward_rate=0.02)
        assert isinstance(results, list)

        # All returned cards should have base rate >= 0.02
        for card_id in results:
            card = db.get_card(card_id)
            assert card["base_rewards_rate"] >= 0.02

    def test_search_cards_max_annual_fee(self):
        """Test searching cards by maximum annual fee."""
        db = CardDatabase()

        results = db.search_cards(max_annual_fee=100)
        assert isinstance(results, list)

        # All returned cards should have annual fee <= 100
        for card_id in results:
            card = db.get_card(card_id)
            assert card["annual_fee"] <= 100

    def test_search_cards_by_issuers(self):
        """Test searching cards by specific issuers."""
        db = CardDatabase()

        results = db.search_cards(issuers=["Chase"])
        assert isinstance(results, list)

        # All returned cards should be from Chase
        for card_id in results:
            card = db.get_card(card_id)
            assert card["issuer"] == "Chase"

    def test_search_cards_by_categories(self):
        """Test searching cards by categories with bonuses."""
        db = CardDatabase()

        results = db.search_cards(categories=["travel"])
        assert isinstance(results, list)

        # All returned cards should have travel category bonus
        for card_id in results:
            card = db.get_card(card_id)
            assert "travel" in card.get("category_bonuses", {})

    def test_search_cards_multiple_criteria(self):
        """Test searching cards with multiple criteria."""
        db = CardDatabase()

        results = db.search_cards(
            min_reward_rate=0.01,
            max_annual_fee=500,
            issuers=["Chase", "American Express"],
            categories=["travel", "dining"],
        )
        assert isinstance(results, list)

        # All returned cards should meet all criteria
        for card_id in results:
            card = db.get_card(card_id)
            assert card["base_rewards_rate"] >= 0.01
            assert card["annual_fee"] <= 500
            assert card["issuer"] in ["Chase", "American Express"]

            card_categories = set(card.get("category_bonuses", {}).keys())
            assert card_categories.intersection({"travel", "dining"})

    def test_search_cards_no_matches(self):
        """Test searching cards with criteria that match nothing."""
        db = CardDatabase()

        results = db.search_cards(
            min_reward_rate=1.0,  # Unrealistically high
            max_annual_fee=0,
            issuers=["Nonexistent Bank"],
        )
        assert isinstance(results, list)
        assert len(results) == 0

    def test_search_cards_empty_lists(self):
        """Test searching cards with empty list criteria."""
        db = CardDatabase()

        results = db.search_cards(issuers=[], categories=[])
        assert isinstance(results, list)
        # Empty lists are falsy, so they don't filter - should return all cards
        assert len(results) > 0

    def test_search_cards_none_values(self):
        """Test searching cards with None values for optional parameters."""
        db = CardDatabase()

        results = db.search_cards(
            min_reward_rate=None, max_annual_fee=None, issuers=None, categories=None
        )
        assert isinstance(results, list)
        assert len(results) > 0


class TestCardDatabaseEdgeCases:
    """Test edge cases and error conditions."""

    def test_database_immutability(self):
        """Test that returned data structures are copies, not references."""
        db = CardDatabase()

        # Test cards copy
        all_cards = db.get_all_cards()
        original_count = len(all_cards)
        all_cards["test_card"] = {"name": "Test"}
        assert len(db.get_all_cards()) == original_count

        # Test categories copy
        all_categories = db.get_all_categories()
        original_count = len(all_categories)
        all_categories["test_category"] = {"description": "Test"}
        assert len(db.get_all_categories()) == original_count

    def test_card_data_types(self):
        """Test that card data has correct types."""
        db = CardDatabase()

        for _card_id, card_data in db.cards.items():
            assert isinstance(card_data["name"], str)
            assert isinstance(card_data["issuer"], str)
            assert isinstance(card_data["annual_fee"], int)
            assert isinstance(card_data["base_rewards_rate"], (int, float))
            assert isinstance(card_data["signup_bonus_points"], int)
            assert isinstance(card_data["signup_bonus_value"], int)
            assert isinstance(card_data["category_bonuses"], dict)
            assert isinstance(card_data["travel_benefits"], list)
            assert isinstance(card_data["foreign_transaction_fee"], (int, float))
            assert isinstance(card_data["credit_score_required"], str)
            assert isinstance(card_data["intro_apr"], (int, float))
            assert isinstance(card_data["intro_period_months"], int)

    def test_category_data_types(self):
        """Test that category data has correct types."""
        db = CardDatabase()

        for _category_id, category_data in db.categories.items():
            assert isinstance(category_data["description"], str)
            assert isinstance(category_data["subcategories"], list)

    def test_reward_rate_calculation_edge_cases(self):
        """Test reward rate calculation with edge cases."""
        db = CardDatabase()

        # Test with None category
        rate = db.calculate_effective_reward_rate("chase_sapphire_preferred", None)
        assert isinstance(rate, float)
        assert rate > 0

    def test_search_with_invalid_types(self):
        """Test search with invalid parameter types."""
        db = CardDatabase()

        # The method doesn't validate types, so invalid types will cause exceptions
        # This is expected behavior - the method assumes correct types
        with pytest.raises(TypeError):
            db.search_cards(min_reward_rate="invalid")

    def test_get_cards_by_annual_fee_negative(self):
        """Test getting cards with negative annual fee limit."""
        db = CardDatabase()

        results = db.get_cards_by_annual_fee(-1)
        assert isinstance(results, list)
        assert len(results) == 0


class TestGetCardDatabaseFunction:
    """Test the get_card_database function."""

    def test_get_card_database_returns_list(self):
        """Test that get_card_database returns a list."""
        cards = get_card_database()
        assert isinstance(cards, list)
        assert len(cards) > 0

    def test_get_card_database_contains_card_data(self):
        """Test that returned cards contain expected data."""
        cards = get_card_database()

        # Find a specific card
        chase_card = None
        for card in cards:
            if card.get("id") == "chase_sapphire_preferred":
                chase_card = card
                break

        assert chase_card is not None
        assert chase_card["name"] == "Chase Sapphire Preferred"
        assert "id" in chase_card

    def test_get_card_database_all_cards_have_id(self):
        """Test that all returned cards have an ID field."""
        cards = get_card_database()

        for card in cards:
            assert "id" in card
            assert isinstance(card["id"], str)
            assert len(card["id"]) > 0

    def test_get_card_database_immutable(self):
        """Test that modifying returned data doesn't affect database."""
        cards = get_card_database()
        original_count = len(cards)

        # Modify the returned list
        cards.append({"id": "test", "name": "Test Card"})

        # Get fresh data
        fresh_cards = get_card_database()
        assert len(fresh_cards) == original_count

    def test_get_card_database_consistency(self):
        """Test that multiple calls return consistent data."""
        cards1 = get_card_database()
        cards2 = get_card_database()

        assert len(cards1) == len(cards2)

        # Check that card IDs are consistent
        ids1 = {card["id"] for card in cards1}
        ids2 = {card["id"] for card in cards2}
        assert ids1 == ids2


class TestCardDatabaseIntegration:
    """Integration tests for card database functionality."""

    def test_full_workflow_card_recommendation(self):
        """Test a full workflow of finding cards for a specific use case."""
        db = CardDatabase()

        # Find cards for travel with low annual fee
        travel_cards = db.get_cards_with_category_bonus("travel")
        low_fee_cards = db.get_cards_by_annual_fee(200)

        # Find intersection
        recommended_cards = [card for card in travel_cards if card in low_fee_cards]

        assert isinstance(recommended_cards, list)

        # Verify all recommended cards meet criteria
        for card_id in recommended_cards:
            card = db.get_card(card_id)
            assert "travel" in card.get("category_bonuses", {})
            assert card["annual_fee"] <= 200

    def test_reward_rate_comparison(self):
        """Test comparing reward rates across different cards."""
        db = CardDatabase()

        # Get all cards and their base rates
        all_cards = db.get_all_cards()
        rates = {}

        for card_id in all_cards:
            rate = db.calculate_effective_reward_rate(card_id)
            rates[card_id] = rate

        assert len(rates) > 0
        assert all(isinstance(rate, float) for rate in rates.values())
        assert all(rate >= 0 for rate in rates.values())

    def test_category_bonus_analysis(self):
        """Test analyzing category bonuses across all cards."""
        db = CardDatabase()

        # Get all categories that have bonuses
        all_cards = db.get_all_cards()
        categories_with_bonuses = set()

        for _card_id, card_data in all_cards.items():
            categories_with_bonuses.update(card_data.get("category_bonuses", {}).keys())

        assert len(categories_with_bonuses) > 0

        # Verify each category has at least one card with bonus
        for category in categories_with_bonuses:
            cards_with_bonus = db.get_cards_with_category_bonus(category)
            assert len(cards_with_bonus) > 0

    def test_issuer_analysis(self):
        """Test analyzing cards by issuer."""
        db = CardDatabase()

        # Get all unique issuers
        all_cards = db.get_all_cards()
        issuers = {card_data["issuer"] for card_data in all_cards.values()}

        assert len(issuers) > 0

        # Verify each issuer has at least one card
        for issuer in issuers:
            issuer_cards = db.get_cards_by_issuer(issuer)
            assert len(issuer_cards) > 0

    def test_search_performance_with_large_criteria(self):
        """Test search performance with many criteria."""
        db = CardDatabase()

        # Test with many criteria
        results = db.search_cards(
            min_reward_rate=0.01,
            max_annual_fee=1000,
            issuers=["Chase", "American Express", "Citi"],
            categories=["travel", "dining", "grocery_stores", "gas_stations"],
        )

        assert isinstance(results, list)

        # Verify results meet all criteria
        for card_id in results:
            card = db.get_card(card_id)
            assert card["base_rewards_rate"] >= 0.01
            assert card["annual_fee"] <= 1000
            assert card["issuer"] in ["Chase", "American Express", "Citi"]

            card_categories = set(card.get("category_bonuses", {}).keys())
            search_categories = {"travel", "dining", "grocery_stores", "gas_stations"}
            assert card_categories.intersection(search_categories)
