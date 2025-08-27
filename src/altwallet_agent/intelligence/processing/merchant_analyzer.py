"""Merchant analyzer for AltWallet Checkout Agent.

This module provides intelligent merchant analysis capabilities including
categorization, risk assessment, and behavior patterns.
"""

from typing import Any, Dict, List, Optional

import structlog

from ...data.card_database import CardDatabase


class MerchantAnalyzer:
    """Intelligent merchant analysis and categorization.
    
    This analyzer provides sophisticated merchant analysis including:
    - Automatic merchant categorization
    - Risk pattern detection
    - Category-specific scoring
    - Historical behavior analysis
    
    Attributes:
        logger: Structured logger instance
        card_db: Card database for category matching
        risk_patterns: Known risk patterns for merchants
    """

    def __init__(self, card_db: Optional[CardDatabase] = None):
        """Initialize the merchant analyzer.
        
        Args:
            card_db: Optional card database for category matching.
                    If None, creates a new instance.
        """
        self.logger = structlog.get_logger(__name__)
        self.card_db = card_db or CardDatabase()
        self.risk_patterns = self._initialize_risk_patterns()

    def _initialize_risk_patterns(self) -> Dict[str, Any]:
        """Initialize known risk patterns for merchant analysis.
        
        Returns:
            Dict[str, Any]: Dictionary of risk patterns and their metadata
        """
        return {
            "high_risk_merchants": [
                "casino", "gambling", "bet", "lottery", "crypto",
                "forex", "bitcoin", "ethereum", "cryptocurrency",
            ],
            "mid_risk_merchants": [
                "wire_transfer", "money_order", "prepaid_card",
                "gift_card", "cash_advance",
            ],
            "foreign_merchants": [
                "foreign", "international", "overseas",
                ".co.uk", ".de", ".jp", ".cn",
            ],
        }

    def analyze_merchant(self, merchant_id: str) -> Dict[str, Any]:
        """Perform comprehensive merchant analysis.
        
        Args:
            merchant_id: Merchant identifier to analyze
            
        Returns:
            Dict[str, Any]: Comprehensive merchant analysis results
        """
        self.logger.debug("Analyzing merchant", merchant_id=merchant_id)
        
        # Detect merchant category
        category = self._detect_merchant_category(merchant_id)
        
        # Assess risk level
        risk_level = self._assess_merchant_risk(merchant_id)
        
        # Get category-specific insights
        category_insights = self._get_category_insights(category)
        
        # Detect behavior patterns
        behavior_patterns = self._detect_behavior_patterns(merchant_id)
        
        analysis_result = {
            "merchant_id": merchant_id,
            "detected_category": category,
            "risk_level": risk_level,
            "category_insights": category_insights,
            "behavior_patterns": behavior_patterns,
            "confidence_score": self._calculate_analysis_confidence(
                merchant_id, category, risk_level
            ),
        }
        
        self.logger.debug(
            "Merchant analysis completed",
            merchant_id=merchant_id,
            category=category,
            risk_level=risk_level,
        )
        
        return analysis_result

    def _detect_merchant_category(self, merchant_id: str) -> str:
        """Detect merchant category based on merchant ID.
        
        Args:
            merchant_id: Merchant identifier
            
        Returns:
            str: Detected merchant category
        """
        merchant_lower = merchant_id.lower()
        
        # Amazon and online shopping
        if "amazon" in merchant_lower or "amzn" in merchant_lower:
            return "online_shopping"
        
        # Travel-related merchants
        if any(keyword in merchant_lower for keyword in [
            "airline", "hotel", "resort", "travel", "trip",
            "booking", "expedia", "orbitz", "priceline",
        ]):
            return "travel"
        
        # Dining and restaurants
        if any(keyword in merchant_lower for keyword in [
            "restaurant", "dining", "cafe", "grill", "pizza",
            "subway", "mcdonalds", "burger", "taco",
        ]):
            return "dining"
        
        # Grocery stores
        if any(keyword in merchant_lower for keyword in [
            "grocery", "supermarket", "food", "market",
            "safeway", "kroger", "whole_food", "trader_joe",
        ]):
            return "grocery_stores"
        
        # Gas stations
        if any(keyword in merchant_lower for keyword in [
            "gas", "fuel", "station", "shell", "exxon", "bp",
            "chevron", "mobil", "texaco",
        ]):
            return "gas_stations"
        
        # Drugstores
        if any(keyword in merchant_lower for keyword in [
            "pharmacy", "drugstore", "cvs", "walgreens",
            "rite_aid", "drug",
        ]):
            return "drugstores"
        
        # Utilities
        if any(keyword in merchant_lower for keyword in [
            "utility", "electric", "water", "gas_company",
            "internet", "cable", "phone",
        ]):
            return "utilities"
        
        # Default category
        return "general_retail"

    def _assess_merchant_risk(self, merchant_id: str) -> str:
        """Assess risk level for a merchant.
        
        Args:
            merchant_id: Merchant identifier
            
        Returns:
            str: Risk level ('low', 'medium', 'high')
        """
        merchant_lower = merchant_id.lower()
        
        # Check for high-risk patterns
        high_risk_keywords = self.risk_patterns["high_risk_merchants"]
        if any(keyword in merchant_lower for keyword in high_risk_keywords):
            return "high"
        
        # Check for medium-risk patterns
        mid_risk_keywords = self.risk_patterns["mid_risk_merchants"]
        if any(keyword in merchant_lower for keyword in mid_risk_keywords):
            return "medium"
        
        # Check for foreign merchants
        foreign_keywords = self.risk_patterns["foreign_merchants"]
        if any(keyword in merchant_lower for keyword in foreign_keywords):
            return "medium"
        
        # Default to low risk for recognized categories
        return "low"

    def _get_category_insights(self, category: str) -> Dict[str, Any]:
        """Get insights specific to a merchant category.
        
        Args:
            category: Merchant category
            
        Returns:
            Dict[str, Any]: Category-specific insights
        """
        category_info = self.card_db.get_category_info(category)
        
        if not category_info:
            return {"description": "Unknown category", "subcategories": []}
        
        # Get cards that offer bonuses for this category
        bonus_cards = self.card_db.get_cards_with_category_bonus(category)
        
        return {
            "description": category_info["description"],
            "subcategories": category_info["subcategories"],
            "cards_with_bonuses": bonus_cards,
            "typical_reward_rate": self._calculate_typical_reward_rate(category),
        }

    def _calculate_typical_reward_rate(self, category: str) -> float:
        """Calculate typical reward rate for a category.
        
        Args:
            category: Merchant category
            
        Returns:
            float: Typical reward rate as a decimal
        """
        bonus_cards = self.card_db.get_cards_with_category_bonus(category)
        
        if not bonus_cards:
            return 0.02  # Default rate
        
        # Calculate average bonus rate for the category
        total_bonus_rate = 0.0
        count = 0
        
        for card_id in bonus_cards:
            card_data = self.card_db.get_card(card_id)
            if card_data and category in card_data.get("category_bonuses", {}):
                total_bonus_rate += card_data["category_bonuses"][category]
                count += 1
        
        if count > 0:
            return total_bonus_rate / count
        
        return 0.02

    def _detect_behavior_patterns(self, merchant_id: str) -> List[str]:
        """Detect behavior patterns for a merchant.
        
        Args:
            merchant_id: Merchant identifier
            
        Returns:
            List[str]: List of detected behavior patterns
        """
        patterns = []
        
        # Check for online-only merchants
        if "online" in merchant_id.lower() or ".com" in merchant_id.lower():
            patterns.append("online_only")
        
        # Check for subscription patterns
        if any(keyword in merchant_id.lower() for keyword in [
            "subscription", "recurring", "monthly", "annual",
        ]):
            patterns.append("subscription_based")
        
        # Check for marketplace patterns
        if any(keyword in merchant_id.lower() for keyword in [
            "marketplace", "platform", "aggregator",
        ]):
            patterns.append("marketplace")
        
        # Check for seasonal patterns
        if any(keyword in merchant_id.lower() for keyword in [
            "christmas", "holiday", "seasonal", "limited",
        ]):
            patterns.append("seasonal_merchant")
        
        return patterns

    def _calculate_analysis_confidence(
        self, merchant_id: str, category: str, risk_level: str
    ) -> float:
        """Calculate confidence score for merchant analysis.
        
        Args:
            merchant_id: Merchant identifier
            category: Detected category
            risk_level: Assessed risk level
            
        Returns:
            float: Confidence score between 0.0 and 1.0
        """
        confidence = 0.5  # Base confidence
        
        # Category confidence
        category_keywords = {
            "online_shopping": ["amazon", "amzn", "online", "ecommerce"],
            "travel": ["airline", "hotel", "travel", "booking"],
            "dining": ["restaurant", "dining", "cafe", "grill"],
            "grocery_stores": ["grocery", "supermarket", "food"],
            "gas_stations": ["gas", "fuel", "station"],
            "drugstores": ["pharmacy", "drugstore", "cvs"],
            "utilities": ["utility", "electric", "water"],
        }
        
        if category in category_keywords:
            keywords = category_keywords[category]
            if any(keyword in merchant_id.lower() for keyword in keywords):
                confidence += 0.3
        
        # Risk level confidence
        if risk_level == "low":
            confidence += 0.1
        elif risk_level == "high":
            confidence += 0.2  # High confidence in detecting high risk
        
        return min(confidence, 1.0)

    def get_optimal_cards_for_merchant(
        self, merchant_id: str, amount: float, max_annual_fee: Optional[int] = None
    ) -> List[str]:
        """Get optimal cards for a specific merchant and transaction.
        
        Args:
            merchant_id: Merchant identifier
            amount: Transaction amount
            max_annual_fee: Maximum annual fee allowed
            
        Returns:
            List[str]: List of optimal card IDs
        """
        analysis = self.analyze_merchant(merchant_id)
        category = analysis["detected_category"]
        
        # Get cards with category bonuses
        bonus_cards = self.card_db.get_cards_with_category_bonus(category)
        
        # Filter by annual fee if specified
        if max_annual_fee is not None:
            affordable_cards = self.card_db.get_cards_by_annual_fee(max_annual_fee)
            bonus_cards = [card for card in bonus_cards if card in affordable_cards]
        
        # If no bonus cards, fall back to high base rate cards
        if not bonus_cards:
            bonus_cards = self.card_db.search_cards(
                min_reward_rate=0.02,
                max_annual_fee=max_annual_fee,
            )
        
        return bonus_cards[:5]  # Return top 5 recommendations
