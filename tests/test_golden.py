"""Golden regression tests for the AltWallet Checkout Agent.

This module provides comprehensive regression testing using golden fixtures
and snapshots to ensure scoring consistency across changes.
"""

import json
import os
from decimal import Decimal
from pathlib import Path
from typing import Dict, Any, List

from altwallet_agent.approval_scorer import ApprovalScorer
from altwallet_agent.composite_utility import CompositeUtility
from altwallet_agent.models import (
    Context,
    Customer,
    Merchant,
    Cart,
    CartItem,
    Device,
    Geo,
    LoyaltyTier,
)


class GoldenRegressionTest:
    """Golden regression test suite for scoring consistency."""

    def __init__(self):
        """Initialize the golden regression test suite."""
        self.fixtures_dir = Path(__file__).parent / "golden" / "fixtures"
        self.snapshots_dir = Path(__file__).parent / "golden" / "snapshots"
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

    def load_fixture(self, fixture_name: str) -> Dict[str, Any]:
        """Load a fixture from the fixtures directory."""
        fixture_path = self.fixtures_dir / f"{fixture_name}.json"
        with open(fixture_path, "r") as f:
            return json.load(f)

    def load_snapshot(self, snapshot_name: str) -> Dict[str, Any]:
        """Load a snapshot from the snapshots directory."""
        snapshot_path = self.snapshots_dir / f"{snapshot_name}.json"
        with open(snapshot_path, "r") as f:
            return json.load(f)

    def save_snapshot(self, snapshot_name: str, data: Dict[str, Any]):
        """Save a snapshot to the snapshots directory."""
        snapshot_path = self.snapshots_dir / f"{snapshot_name}.json"
        with open(snapshot_path, "w") as f:
            json.dump(data, f, indent=2)

    def fixture_to_context(self, fixture_data: Dict[str, Any]) -> Context:
        """Convert fixture data to Context object."""
        customer_data = fixture_data.get("customer", {})
        merchant_data = fixture_data.get("merchant", {})
        cart_data = fixture_data.get("cart", {})
        device_data = fixture_data.get("device", {})
        geo_data = fixture_data.get("geo", {})

        # Create customer
        customer = Customer(
            id=customer_data.get("id", "unknown"),
            loyalty_tier=LoyaltyTier(customer_data.get("loyalty_tier", "NONE")),
            historical_velocity_24h=customer_data.get("historical_velocity_24h", 0),
            chargebacks_12m=customer_data.get("chargebacks_12m", 0),
        )

        # Create merchant
        merchant = Merchant(
            name=merchant_data.get("name", "Unknown"),
            mcc=merchant_data.get("mcc", "0000"),
            network_preferences=merchant_data.get("network_preferences", []),
            location=merchant_data.get("location", {}),
        )

        # Create cart
        cart_items = []
        for item_data in cart_data.get("items", []):
            cart_items.append(
                CartItem(
                    item=item_data.get("name", "Unknown"),
                    unit_price=Decimal(str(item_data.get("price", "0.00"))),
                    qty=item_data.get("quantity", 1),
                )
            )

        cart = Cart(
            items=cart_items,
            total_amount=Decimal(str(cart_data.get("total_amount", "0.00"))),
        )

        # Create device
        device = Device(
            ip=device_data.get("ip", "0.0.0.0"),
            location=device_data.get("location", {}),
        )

        # Create geo
        geo = Geo(
            city=geo_data.get("city", "Unknown"),
            country=geo_data.get("country", "US"),
        )

        return Context(
            customer=customer,
            merchant=merchant,
            cart=cart,
            device=device,
            geo=geo,
        )

    def run_scoring(self, context: Context) -> Dict[str, Any]:
        """Run scoring and return results."""
        # Convert context to dict for approval scorer
        context_dict = {
            "mcc": context.merchant.mcc,
            "amount": context.cart.total,
            "issuer_family": "visa",  # Default
            "cross_border": getattr(context, "cross_border", False),
            "location_mismatch_distance": (
                self._calculate_location_mismatch_distance(context)
            ),
            "velocity_24h": getattr(context, "velocity_24h", 0),
            "velocity_7d": getattr(context, "velocity_7d", 0),
            "chargebacks_12m": context.customer.chargebacks_12m,
            "merchant_risk_tier": getattr(context.merchant, "risk_tier", "low"),
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

        # Extract top feature drivers from attributions
        top_feature_drivers = self._extract_feature_drivers(
            approval_result.attributions
        )

        return {
            "p_approval": round(approval_result.p_approval, 2),
            "top_card": top_card,
            "utility": round(top_utility, 4),
            "top_feature_drivers": top_feature_drivers,
            "raw_score": round(approval_result.raw_score, 1),
            "calibration_method": approval_result.calibration["method"],
            "risk_signals": self._extract_risk_signals(context),
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

    def _extract_feature_drivers(self, attributions) -> List[Dict[str, Any]]:
        """Extract top feature drivers from attributions."""
        if not attributions:
            return []

        # Convert attributions to list of dicts
        drivers = []
        for attr_name, value in vars(attributions).items():
            if attr_name.startswith("_") or attr_name in [
                "baseline",
                "contribs",
                "sum",
            ]:
                continue
            if isinstance(value, (int, float)) and value != 0:
                drivers.append(
                    {
                        "feature": attr_name,
                        "contribution": round(value, 1),
                        "description": f"{attr_name.replace('_', ' ').title()} contribution",
                    }
                )

        # Sort by absolute contribution and take top 4
        drivers.sort(key=lambda x: abs(x["contribution"]), reverse=True)
        return drivers[:4]

    def _extract_risk_signals(self, context: Context) -> Dict[str, bool]:
        """Extract risk signals from context."""
        return {
            "location_mismatch": self._calculate_location_mismatch_distance(context)
            > 0,
            "cross_border": getattr(context, "cross_border", False),
            "high_velocity": getattr(context, "velocity_24h", 0) > 10
            or getattr(context, "velocity_7d", 0) > 50,
            "chargeback_history": context.customer.chargebacks_12m > 0,
        }

    def test_fixture(self, fixture_name: str):
        """Test a single fixture against its snapshot."""
        # Load fixture and snapshot
        fixture_data = self.load_fixture(fixture_name)
        expected_snapshot = self.load_snapshot(fixture_name)

        # Convert fixture to context
        context = self.fixture_to_context(fixture_data)

        # Run scoring
        actual_result = self.run_scoring(context)

        # Check if we should update golden
        if os.environ.get("UPDATE_GOLDEN") == "1":
            self.save_snapshot(fixture_name, actual_result)
            print(f"Updated golden snapshot for {fixture_name}")
            return

        # Assert results match
        assert (
            actual_result["p_approval"] == expected_snapshot["p_approval"]
        ), f"p_approval mismatch for {fixture_name}"

        assert (
            actual_result["top_card"] == expected_snapshot["top_card"]
        ), f"top_card mismatch for {fixture_name}"

        assert (
            abs(actual_result["utility"] - expected_snapshot["utility"]) < 0.001
        ), f"utility mismatch for {fixture_name}"

        assert (
            actual_result["raw_score"] == expected_snapshot["raw_score"]
        ), f"raw_score mismatch for {fixture_name}"

        assert (
            actual_result["calibration_method"]
            == expected_snapshot["calibration_method"]
        ), f"calibration_method mismatch for {fixture_name}"


# Create test instances for each fixture
test_suite = GoldenRegressionTest()


def test_01_grocery_small_ticket():
    """Test grocery small ticket fixture."""
    test_suite.test_fixture("01_grocery_small_ticket")


def test_02_travel_high_value():
    """Test travel high value fixture."""
    test_suite.test_fixture("02_travel_high_value")


def test_03_cross_border():
    """Test cross-border fixture."""
    test_suite.test_fixture("03_cross_border")


def test_04_device_mismatch_high_velocity():
    """Test device mismatch high velocity fixture."""
    test_suite.test_fixture("04_device_mismatch_high_velocity")


def test_05_loyalty_gold_with_promo():
    """Test loyalty gold with promo fixture."""
    test_suite.test_fixture("05_loyalty_gold_with_promo")


def test_06_merchant_prefers_debit():
    """Test merchant prefers debit fixture."""
    test_suite.test_fixture("06_merchant_prefers_debit")


def test_07_high_risk_mcc():
    """Test high risk MCC fixture."""
    test_suite.test_fixture("07_high_risk_mcc")


def test_08_missing_fields():
    """Test missing fields fixture."""
    test_suite.test_fixture("08_missing_fields")


def test_09_issuer_affinity():
    """Test issuer affinity fixture."""
    test_suite.test_fixture("09_issuer_affinity")


def test_10_mixed_cart_large_amount():
    """Test mixed cart large amount fixture."""
    test_suite.test_fixture("10_mixed_cart_large_amount")


if __name__ == "__main__":
    # Run all tests
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "update":
        os.environ["UPDATE_GOLDEN"] = "1"
        print("Updating golden snapshots...")

    # Run all fixture tests
    fixture_names = [
        "grocery_small_ticket",
        "travel_high_value",
        "cross_border",
        "device_mismatch_high_velocity",
        "loyalty_gold_with_promo",
        "merchant_prefers_debit",
        "high_risk_mcc",
        "missing_fields",
        "issuer_affinity",
        "mixed_cart_large_amount",
    ]
    for i in range(1, 11):
        fixture_name = f"{i:02d}_{fixture_names[i-1]}"
        test_suite.test_fixture(fixture_name)

    print("All golden regression tests passed!")
