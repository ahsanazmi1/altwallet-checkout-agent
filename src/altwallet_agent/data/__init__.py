"""Data layer for AltWallet Checkout Agent.

This package provides data components including card databases,
merchant categorization, and risk patterns.
"""

from .card_database import CardDatabase

__all__ = ["CardDatabase"]
