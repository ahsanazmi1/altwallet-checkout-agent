"""Core functionality for AltWallet Merchant Agent."""

from dataclasses import dataclass
from typing import List, Optional
from decimal import Decimal


@dataclass
class Card:
    """Represents a credit card with its properties."""
    name: str
    cashback_rate: Decimal
    annual_fee: Decimal
    category_bonus: Optional[str] = None
    category_multiplier: Decimal = Decimal('1.0')


@dataclass
class Purchase:
    """Represents a purchase transaction."""
    amount: Decimal
    category: str
    merchant: str


class CardRecommender:
    """Deterministic card recommendation engine."""
    
    def __init__(self):
        self.cards = [
            Card("Chase Freedom Unlimited", Decimal('0.015'), Decimal('0')),
            Card("Chase Sapphire Preferred", Decimal('0.01'), Decimal('95'), "travel", Decimal('2.5')),
            Card("Citi Double Cash", Decimal('0.02'), Decimal('0')),
            Card("Amex Blue Cash Preferred", Decimal('0.01'), Decimal('95'), "groceries", Decimal('6.0')),
        ]
    
    def get_best_card(self, purchase: Purchase) -> Card:
        """
        Determine the best card for a given purchase.
        
        Args:
            purchase: The purchase details
            
        Returns:
            The recommended card
        """
        best_card = None
        best_value = Decimal('-inf')
        
        for card in self.cards:
            # Calculate effective cashback rate
            if card.category_bonus and card.category_bonus in purchase.category.lower():
                effective_rate = card.cashback_rate * card.category_multiplier
            else:
                effective_rate = card.cashback_rate
            
            # Calculate net value (cashback - annual fee)
            cashback_value = purchase.amount * effective_rate
            net_value = cashback_value - (card.annual_fee / Decimal('12'))  # Monthly fee
            
            if net_value > best_value:
                best_value = net_value
                best_card = card
        
        return best_card or self.cards[0]  # Fallback to first card
    
    def apply_p_approval(self, score: float, p_approval: float) -> float:
        """
        Apply probability approval multiplier to score.
        
        Args:
            score: Base score to adjust
            p_approval: Probability approval multiplier (0-1)
            
        Returns:
            Adjusted score
        """
        if not 0 <= p_approval <= 1:
            raise ValueError("p_approval must be between 0 and 1")
        return score * p_approval
    
    def apply_geo_promo(self, rewards_value: Decimal) -> Decimal:
        """
        Apply geographic promotion bonus to rewards value.
        
        Args:
            rewards_value: Base rewards value
            
        Returns:
            Rewards value with geo promo bonus
        """
        geo_promo_bonus = Decimal('1.50')
        return rewards_value + geo_promo_bonus
