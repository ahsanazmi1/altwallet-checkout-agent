#!/usr/bin/env python3
"""Smoke tests for the AltWallet Checkout Agent.

This module runs 3 representative scenarios and emits compact JSON lines
for CI integration and monitoring.
"""

import json
import sys
from pathlib import Path
from typing import Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from decimal import Decimal

from altwallet_agent.approval_scorer import ApprovalScorer
from altwallet_agent.composite_utility import CompositeUtility
from altwallet_agent.models import (
    Cart,
    CartItem,
    Context,
    Customer,
    Device,
    Geo,
    LoyaltyTier,
    Merchant,
)


class SmokeTester:
    """Smoke test runner for representative scenarios."""

    def __init__(self):
        """Initialize the smoke tester."""
        self.approval_scorer = ApprovalScorer()
        self.composite_utility = CompositeUtility()

        # Sample cards for utility testing
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
        ]

    def create_grocery_scenario(self) -> Context:
        """Create a grocery shopping scenario."""
        return Context(
            customer=Customer(
                id="smoke_grocery",
                loyalty_tier=LoyaltyTier.SILVER,
                historical_velocity_24h=2,
                chargebacks_12m=0,
            ),
            merchant=Merchant(
                name="Local Grocery Store",
                mcc="5411",
                network_preferences=["visa", "mastercard"],
                location={"city": "Austin", "country": "US"},
            ),
            cart=Cart(
                items=[
                    CartItem(item="Organic Bananas", unit_price=Decimal("3.99"), qty=1),
                    CartItem(item="Whole Milk", unit_price=Decimal("4.50"), qty=1),
                ],
            ),
            device=Device(
                ip="192.168.1.100", location={"city": "Austin", "country": "US"}
            ),
            geo=Geo(city="Austin", country="US"),
        )

    def create_travel_scenario(self) -> Context:
        """Create a travel booking scenario."""
        return Context(
            customer=Customer(
                id="smoke_travel",
                loyalty_tier=LoyaltyTier.PLATINUM,
                historical_velocity_24h=1,
                chargebacks_12m=0,
            ),
            merchant=Merchant(
                name="Travel Agency",
                mcc="4722",
                network_preferences=["american_express", "visa"],
                location={"city": "Miami", "country": "US"},
            ),
            cart=Cart(
                items=[
                    CartItem(
                        item="Flight to Tokyo", unit_price=Decimal("8500.00"), qty=1
                    ),
                    CartItem(
                        item="Hotel Booking", unit_price=Decimal("3200.00"), qty=1
                    ),
                ],
            ),
            device=Device(
                ip="192.168.1.101", location={"city": "Miami", "country": "US"}
            ),
            geo=Geo(city="Miami", country="US"),
        )

    def create_high_risk_scenario(self) -> Context:
        """Create a high-risk transaction scenario."""
        return Context(
            customer=Customer(
                id="smoke_high_risk",
                loyalty_tier=LoyaltyTier.GOLD,
                historical_velocity_24h=15,
                chargebacks_12m=1,
            ),
            merchant=Merchant(
                name="Online Casino",
                mcc="7995",
                network_preferences=["visa", "mastercard"],
                location={"city": "Las Vegas", "country": "US"},
            ),
            cart=Cart(
                items=[
                    CartItem(
                        item="Gaming Credits", unit_price=Decimal("500.00"), qty=1
                    ),
                ],
            ),
            device=Device(
                ip="192.168.1.102", location={"city": "Los Angeles", "country": "US"}
            ),
            geo=Geo(city="Las Vegas", country="US"),
        )

    def run_scenario(self, scenario_name: str, context: Context) -> dict[str, Any]:
        """Run a single scenario and return results."""
        # Convert context to dict for approval scorer
        context_dict = {
            "mcc": context.merchant.mcc,
            "amount": context.cart.total,
            "issuer_family": "visa",  # Default
            "cross_border": False,
            "location_mismatch_distance": self._calculate_location_mismatch_distance(
                context
            ),
            "velocity_24h": context.customer.historical_velocity_24h,
            "velocity_7d": context.customer.historical_velocity_24h * 4,  # Estimate
            "chargebacks_12m": context.customer.chargebacks_12m,
            "merchant_risk_tier": "low",
            "loyalty_tier": context.customer.loyalty_tier.value,
        }

        # Run approval scoring
        approval_result = self.approval_scorer.score(context_dict)

        # Run composite utility scoring
        ranked_cards = self.composite_utility.rank_cards_by_utility(
            self.sample_cards, context
        )

        # Get top card and utility
        top_card = ranked_cards[0]["card_id"] if ranked_cards else "unknown"
        top_utility = ranked_cards[0]["utility_score"] if ranked_cards else 0.0

        return {
            "scenario": scenario_name,
            "p_approval": round(approval_result.p_approval, 3),
            "top_card": top_card,
            "utility": round(top_utility, 4),
            "raw_score": round(approval_result.raw_score, 1),
            "risk_signals": {
                "location_mismatch": self._calculate_location_mismatch_distance(context)
                > 0,
                "high_velocity": context.customer.historical_velocity_24h > 10,
                "chargeback_history": context.customer.chargebacks_12m > 0,
            },
            "status": "pass" if approval_result.p_approval > 0.005 else "fail",
        }

    def _calculate_location_mismatch_distance(self, context: Context) -> float:
        """Calculate location mismatch distance."""
        try:
            device = context.device
            geo = context.geo

            if (
                device.location.get("city") == geo.city
                and device.location.get("country") == geo.country
            ):
                return 0.0
            elif device.location.get("country") == geo.country:
                return 50.0  # Same country, different city
            else:
                return 200.0  # Different country
        except Exception:
            return 0.0

    def run_all_scenarios(self) -> list:
        """Run all smoke test scenarios."""
        scenarios = [
            ("grocery", self.create_grocery_scenario()),
            ("travel", self.create_travel_scenario()),
            ("high_risk", self.create_high_risk_scenario()),
        ]

        results = []
        for scenario_name, context in scenarios:
            try:
                result = self.run_scenario(scenario_name, context)
                results.append(result)
            except Exception as e:
                results.append(
                    {"scenario": scenario_name, "error": str(e), "status": "error"}
                )

        return results


def main():
    """Main entry point for smoke tests."""
    tester = SmokeTester()
    results = tester.run_all_scenarios()

    # Emit compact JSON lines for CI
    for result in results:
        print(json.dumps(result, separators=(",", ":")))

    # Check for failures
    failed_scenarios = [r for r in results if r.get("status") == "fail"]
    error_scenarios = [r for r in results if r.get("status") == "error"]

    if failed_scenarios or error_scenarios:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
