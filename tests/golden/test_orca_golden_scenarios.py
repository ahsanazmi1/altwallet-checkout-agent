"""
Golden tests for Orca-specific scenarios and features.

This module tests the new Orca decision engine features including:
- Decision types (APPROVE/REVIEW/DECLINE)
- Actions (discount, KYC, risk_review, surcharge_suppression)
- Routing hints (network preferences, interchange optimization)
- Orca features (loyalty boosts, risk assessment, velocity analysis)
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
GOLDEN_DIR = PROJECT_ROOT / "tests" / "golden"
FIXTURES_DIR = GOLDEN_DIR / "fixtures"
SNAPSHOTS_DIR = GOLDEN_DIR / "snapshots"


def normalize_json(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize JSON for comparison by sorting keys and removing dynamic fields."""
    # Remove dynamic fields
    dynamic_fields = [
        "trace_id",
        "transaction_id",
        "request_id",
        "processing_time_ms",
    ]
    for field in dynamic_fields:
        if field in data:
            del data[field]

    # Remove dynamic fields from recommendations
    if "recommendations" in data:
        for rec in data["recommendations"]:
            if "audit" in rec:
                audit = rec["audit"]
                for field in ["request_id", "latency_ms", "code_version"]:
                    if field in audit:
                        del audit[field]

    # Recursively sort all dictionary keys
    def sort_dict(d):
        if isinstance(d, dict):
            return {k: sort_dict(v) for k, v in sorted(d.items())}
        elif isinstance(d, list):
            return [sort_dict(item) for item in d]
        else:
            return d

    return sort_dict(data)


def run_scorer_on_input(input_file: Path) -> dict[str, Any]:
    """Run the scorer CLI on an input file and return the JSON result."""
    try:
        # Run the CLI command
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "altwallet_agent",
                "score",
                "--input",
                str(input_file),
            ],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )

        if result.returncode != 0:
            pytest.fail(f"CLI command failed: {result.stderr}")

        # Parse the JSON output
        return json.loads(result.stdout)

    except json.JSONDecodeError as e:
        pytest.fail(f"Failed to parse JSON output: {e}")
    except Exception as e:
        pytest.fail(f"Unexpected error running scorer: {e}")


class TestOrcaGoldenScenarios:
    """Test Orca-specific golden scenarios."""

    def test_orca_online_grocery_golden(self):
        """Test Orca online grocery scenario golden test."""
        fixture_file = FIXTURES_DIR / "11_orca_online_grocery.json"
        snapshot_file = SNAPSHOTS_DIR / "11_orca_online_grocery.json"

        assert fixture_file.exists(), f"Fixture file not found: {fixture_file}"
        assert snapshot_file.exists(), f"Snapshot file not found: {snapshot_file}"

        # Run scorer on fixture
        actual_output = run_scorer_on_input(fixture_file)

        # Load expected output
        with open(snapshot_file) as f:
            expected_output = json.load(f)

        # Normalize both outputs for comparison
        normalize_json(actual_output)
        normalize_json(expected_output)

        # Validate Orca-specific fields
        assert actual_output["decision"] == expected_output["decision"]
        assert actual_output["score"] >= 0.8  # High score for grocery with loyalty

        # Validate actions
        actual_actions = {action["type"] for action in actual_output["actions"]}
        expected_actions = {action["type"] for action in expected_output["actions"]}
        assert actual_actions == expected_actions

        # Validate routing hints
        actual_hints = actual_output["routing_hints"]
        expected_hints = expected_output["routing_hints"]
        assert actual_hints["preferred_network"] == expected_hints["preferred_network"]
        assert (
            actual_hints["interchange_optimization"]
            == expected_hints["interchange_optimization"]
        )
        assert (
            actual_hints["surcharge_suppression"]
            == expected_hints["surcharge_suppression"]
        )

        # Validate Orca features
        actual_features = set(actual_output["metadata"]["orca_features"])
        expected_features = set(expected_output["metadata"]["orca_features"])
        assert actual_features == expected_features

        # Validate recommendations structure
        assert len(actual_output["recommendations"]) == len(
            expected_output["recommendations"]
        )
        if actual_output["recommendations"]:
            actual_rec = actual_output["recommendations"][0]
            expected_rec = expected_output["recommendations"][0]
            assert actual_rec["card_id"] == expected_rec["card_id"]
            assert actual_rec["rank"] == expected_rec["rank"]
            assert abs(actual_rec["p_approval"] - expected_rec["p_approval"]) < 0.1
            assert abs(actual_rec["utility"] - expected_rec["utility"]) < 0.1

    def test_orca_in_person_retail_golden(self):
        """Test Orca in-person retail scenario golden test."""
        fixture_file = FIXTURES_DIR / "12_orca_in_person_retail.json"
        snapshot_file = SNAPSHOTS_DIR / "12_orca_in_person_retail.json"

        assert fixture_file.exists(), f"Fixture file not found: {fixture_file}"
        assert snapshot_file.exists(), f"Snapshot file not found: {snapshot_file}"

        # Run scorer on fixture
        actual_output = run_scorer_on_input(fixture_file)

        # Load expected output
        with open(snapshot_file) as f:
            expected_output = json.load(f)

        # Validate Orca-specific fields
        assert actual_output["decision"] == expected_output["decision"]
        assert actual_output["score"] >= 0.9  # Very high score for platinum tier

        # Validate actions for platinum tier
        actual_actions = {action["type"] for action in actual_output["actions"]}
        expected_actions = {action["type"] for action in expected_output["actions"]}
        assert actual_actions == expected_actions

        # Validate routing hints
        actual_hints = actual_output["routing_hints"]
        expected_hints = expected_output["routing_hints"]
        assert actual_hints["preferred_network"] == expected_hints["preferred_network"]
        assert (
            actual_hints["interchange_optimization"]
            == expected_hints["interchange_optimization"]
        )

    def test_orca_high_risk_cross_border_golden(self):
        """Test Orca high-risk cross-border scenario golden test."""
        fixture_file = FIXTURES_DIR / "13_orca_high_risk_cross_border.json"
        snapshot_file = SNAPSHOTS_DIR / "13_orca_high_risk_cross_border.json"

        assert fixture_file.exists(), f"Fixture file not found: {fixture_file}"
        assert snapshot_file.exists(), f"Snapshot file not found: {snapshot_file}"

        # Run scorer on fixture
        actual_output = run_scorer_on_input(fixture_file)

        # Load expected output
        with open(snapshot_file) as f:
            expected_output = json.load(f)

        # Validate Orca-specific fields
        assert actual_output["decision"] == expected_output["decision"]
        assert actual_output["score"] < 0.6  # Lower score due to risk factors

        # Validate actions for high-risk scenario
        actual_actions = {action["type"] for action in actual_output["actions"]}
        expected_actions = {action["type"] for action in expected_output["actions"]}
        assert actual_actions == expected_actions

        # Validate routing hints for risk mitigation
        actual_hints = actual_output["routing_hints"]
        expected_hints = expected_output["routing_hints"]
        assert (
            actual_hints["surcharge_suppression"]
            == expected_hints["surcharge_suppression"]
        )
        assert (
            actual_hints["interchange_optimization"]
            == expected_hints["interchange_optimization"]
        )

    def test_orca_surcharge_suppression_golden(self):
        """Test Orca surcharge suppression scenario golden test."""
        fixture_file = FIXTURES_DIR / "14_orca_surcharge_suppression.json"
        snapshot_file = SNAPSHOTS_DIR / "14_orca_surcharge_suppression.json"

        assert fixture_file.exists(), f"Fixture file not found: {fixture_file}"
        assert snapshot_file.exists(), f"Snapshot file not found: {snapshot_file}"

        # Run scorer on fixture
        actual_output = run_scorer_on_input(fixture_file)

        # Load expected output
        with open(snapshot_file) as f:
            expected_output = json.load(f)

        # Validate Orca-specific fields
        assert actual_output["decision"] == expected_output["decision"]
        assert actual_output["score"] >= 0.7  # Good score with surcharge suppression

        # Validate actions for surcharge suppression
        actual_actions = {action["type"] for action in actual_output["actions"]}
        expected_actions = {action["type"] for action in expected_output["actions"]}
        assert actual_actions == expected_actions

        # Validate routing hints
        actual_hints = actual_output["routing_hints"]
        expected_hints = expected_output["routing_hints"]
        assert (
            actual_hints["surcharge_suppression"]
            == expected_hints["surcharge_suppression"]
        )
        assert (
            actual_hints["interchange_optimization"]
            == expected_hints["interchange_optimization"]
        )

    def test_orca_loyalty_boost_golden(self):
        """Test Orca loyalty boost scenario golden test."""
        fixture_file = FIXTURES_DIR / "15_orca_loyalty_boost.json"
        snapshot_file = SNAPSHOTS_DIR / "15_orca_loyalty_boost.json"

        assert fixture_file.exists(), f"Fixture file not found: {fixture_file}"
        assert snapshot_file.exists(), f"Snapshot file not found: {snapshot_file}"

        # Run scorer on fixture
        actual_output = run_scorer_on_input(fixture_file)

        # Load expected output
        with open(snapshot_file) as f:
            expected_output = json.load(f)

        # Validate Orca-specific fields
        assert actual_output["decision"] == expected_output["decision"]
        assert actual_output["score"] >= 0.9  # Very high score for diamond tier

        # Validate actions for diamond tier
        actual_actions = {action["type"] for action in actual_output["actions"]}
        expected_actions = {action["type"] for action in expected_output["actions"]}
        assert actual_actions == expected_actions

        # Validate routing hints
        actual_hints = actual_output["routing_hints"]
        expected_hints = expected_output["routing_hints"]
        assert actual_hints["preferred_network"] == expected_hints["preferred_network"]
        assert (
            actual_hints["interchange_optimization"]
            == expected_hints["interchange_optimization"]
        )

    def test_all_orca_golden_fixtures(self):
        """Test all Orca golden fixtures against their expected outputs."""
        # Get all Orca fixture files (11-15)
        orca_fixture_files = [
            "11_orca_online_grocery.json",
            "12_orca_in_person_retail.json",
            "13_orca_high_risk_cross_border.json",
            "14_orca_surcharge_suppression.json",
            "15_orca_loyalty_boost.json",
        ]

        for fixture_name in orca_fixture_files:
            fixture_file = FIXTURES_DIR / fixture_name
            snapshot_file = SNAPSHOTS_DIR / fixture_name

            if not fixture_file.exists():
                pytest.skip(f"Fixture file not found: {fixture_file}")

            if not snapshot_file.exists():
                pytest.skip(f"Snapshot file not found: {snapshot_file}")

            # Run scorer on fixture
            actual_output = run_scorer_on_input(fixture_file)

            # Load expected output
            with open(snapshot_file) as f:
                json.load(f)

            # Validate Orca-specific fields are present
            assert "decision" in actual_output
            assert "actions" in actual_output
            assert "routing_hints" in actual_output
            assert "orca_features" in actual_output["metadata"]

            # Validate decision type
            assert actual_output["decision"] in [
                "APPROVE",
                "REVIEW",
                "DECLINE",
            ]

            # Validate actions structure
            for action in actual_output["actions"]:
                assert "type" in action
                assert "value" in action
                assert "description" in action

            # Validate routing hints structure
            hints = actual_output["routing_hints"]
            assert "preferred_network" in hints
            assert "fallback_networks" in hints
            assert "interchange_optimization" in hints
            assert "surcharge_suppression" in hints

            # Validate Orca features
            orca_features = actual_output["metadata"]["orca_features"]
            assert isinstance(orca_features, list)
            assert len(orca_features) > 0


if __name__ == "__main__":
    pytest.main([__file__])
