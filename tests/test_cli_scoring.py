#!/usr/bin/env python3
"""Test script for CLI scoring functionality."""

import json
import subprocess
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_cli_scoring_basic():
    """Test CLI scoring with basic context."""
    print("Testing CLI scoring with basic context...")

    # Path to the basic context file
    basic_file = Path(__file__).parent.parent / "examples" / "context_basic.json"

    # Run CLI command
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "altwallet_agent",
            "score",
            "--input",
            str(basic_file),
            "--trace-id",
            "test-basic-123",
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )

    print(f"Exit code: {result.returncode}")
    print(f"Stdout: {result.stdout}")
    if result.stderr:
        print(f"Stderr: {result.stderr}")

    # Parse output - extract the last JSON line (the actual result)
    if result.returncode == 0:
        # Split by lines and find the last JSON object
        lines = result.stdout.strip().split("\n")
        last_json_line = None
        for line in lines:
            if line.strip().startswith("{") and line.strip().endswith("}"):
                last_json_line = line.strip()

        if not last_json_line:
            print("❌ No JSON output found in stdout")
            assert False, "No JSON output found in stdout"

        output = json.loads(last_json_line)
        print(f"Trace ID: {output['trace_id']}")
        print(f"Risk Score: {output['risk_score']}")
        print(f"Loyalty Boost: {output['loyalty_boost']}")
        print(f"Final Score: {output['final_score']}")
        print(f"Routing Hint: {output['routing_hint']}")

        # Verify expected results for basic context
        assert output["risk_score"] == 0  # No risk factors
        assert output["loyalty_boost"] == 5  # SILVER tier
        assert output["final_score"] == 105  # 100 - 0 + 5
        assert output["routing_hint"] == "prefer_mc"  # MCC 5411

        print("✅ Basic context test passed!")
    else:
        print("❌ Basic context test failed!")


def test_cli_scoring_risky():
    """Test CLI scoring with risky context."""
    print("\nTesting CLI scoring with risky context...")

    # Path to the risky context file
    risky_file = Path(__file__).parent.parent / "examples" / "context_risky.json"

    # Run CLI command
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "altwallet_agent",
            "score",
            "--input",
            str(risky_file),
            "--trace-id",
            "test-risky-456",
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )

    print(f"Exit code: {result.returncode}")
    print(f"Stdout: {result.stdout}")
    if result.stderr:
        print(f"Stderr: {result.stderr}")

    # Parse output - extract the last JSON line (the actual result)
    if result.returncode == 0:
        # Split by lines and find the last JSON object
        lines = result.stdout.strip().split("\n")
        last_json_line = None
        for line in lines:
            if line.strip().startswith("{") and line.strip().endswith("}"):
                last_json_line = line.strip()

        if not last_json_line:
            print("❌ No JSON output found in stdout")
            assert False, "No JSON output found in stdout"

        output = json.loads(last_json_line)
        print(f"Trace ID: {output['trace_id']}")
        print(f"Risk Score: {output['risk_score']}")
        print(f"Loyalty Boost: {output['loyalty_boost']}")
        print(f"Final Score: {output['final_score']}")
        print(f"Routing Hint: {output['routing_hint']}")
        print(f"Risk Factors: {output['signals']['risk_factors']}")

        # Verify expected results for risky context
        expected_risk = (
            30 + 20 + 25 + 10
        )  # location + velocity + chargebacks + high_ticket
        assert output["risk_score"] == expected_risk
        assert output["loyalty_boost"] == 0  # NONE tier
        assert output["final_score"] == max(0, 100 - expected_risk) + 0
        assert output["routing_hint"] == "prefer_mc"  # MCC 5732
        assert len(output["signals"]["risk_factors"]) == 4

        print("✅ Risky context test passed!")
    else:
        print("❌ Risky context test failed!")


def test_cli_scoring_pretty():
    """Test CLI scoring with pretty output."""
    print("\nTesting CLI scoring with pretty output...")

    # Path to the basic context file
    basic_file = Path(__file__).parent.parent / "examples" / "context_basic.json"

    # Run CLI command with pretty flag
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "altwallet_agent",
            "score",
            "--input",
            str(basic_file),
            "--pretty",
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )

    print(f"Exit code: {result.returncode}")
    print("Pretty output:")
    print(result.stdout)

    if result.returncode == 0:
        # For pretty output, we need to extract the last JSON object
        # Split by lines and find the last JSON object
        lines = result.stdout.strip().split("\n")
        last_json_line = None
        for line in lines:
            if line.strip().startswith("{") and line.strip().endswith("}"):
                last_json_line = line.strip()

        if not last_json_line:
            print("❌ No JSON output found in stdout")
            assert False, "No JSON output found in stdout"

        # Verify it's valid JSON
        output = json.loads(last_json_line)
        assert "trace_id" in output
        assert "risk_score" in output
        print("✅ Pretty output test passed!")
    else:
        print("❌ Pretty output test failed!")


def test_cli_scoring_stdin():
    """Test CLI scoring with stdin input."""
    print("\nTesting CLI scoring with stdin input...")

    # Read the basic context file
    basic_file = Path(__file__).parent.parent / "examples" / "context_basic.json"
    with open(basic_file) as f:
        json_input = f.read()

    # Run CLI command with stdin
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "altwallet_agent",
            "score",
            "--trace-id",
            "test-stdin-789",
        ],
        input=json_input,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )

    print(f"Exit code: {result.returncode}")
    print(f"Stdout: {result.stdout}")

    if result.returncode == 0:
        # Split by lines and find the last JSON object
        lines = result.stdout.strip().split("\n")
        last_json_line = None
        for line in lines:
            if line.strip().startswith("{") and line.strip().endswith("}"):
                last_json_line = line.strip()

        if not last_json_line:
            print("❌ No JSON output found in stdout")
            assert False, "No JSON output found in stdout"

        output = json.loads(last_json_line)
        assert output["trace_id"] == "test-stdin-789"
        assert output["risk_score"] == 0
        print("✅ Stdin input test passed!")
    else:
        print("❌ Stdin input test failed!")


def main():
    """Run all CLI tests."""
    print("Running AltWallet CLI Scoring Tests")
    print("=" * 50)

    tests = [
        test_cli_scoring_basic,
        test_cli_scoring_risky,
        test_cli_scoring_pretty,
        test_cli_scoring_stdin,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")

    print(f"\n{'='*50}")
    print(f"Tests passed: {passed}/{total}")

    if passed == total:
        print("🎉 All CLI tests passed!")
        return 0
    else:
        print("❌ Some CLI tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
