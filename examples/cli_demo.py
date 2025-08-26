#!/usr/bin/env python3
"""Demonstration of AltWallet CLI functionality."""

import json
import subprocess
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def run_cli_score(input_file, trace_id=None, pretty=False):
    """Run the CLI score command and return results."""
    cmd = [sys.executable, "-m", "altwallet_agent", "score", "--input", str(input_file)]

    if trace_id:
        cmd.extend(["--trace-id", trace_id])

    if pretty:
        cmd.append("--pretty")

    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=Path(__file__).parent.parent
    )

    if result.returncode == 0:
        return json.loads(result.stdout.strip())
    else:
        print(f"CLI Error: {result.stderr}")
        return None


def print_scoring_result(title, result):
    """Print a formatted scoring result."""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")

    if result is None:
        print("❌ Scoring failed")
        return

    print(f"Trace ID: {result['trace_id']}")
    print(f"Risk Score: {result['risk_score']}")
    print(f"Loyalty Boost: +{result['loyalty_boost']}")
    print(f"Final Score: {result['final_score']}")
    print(f"Routing Hint: {result['routing_hint']}")

    signals = result["signals"]
    print(f"\nRisk Factors: {signals.get('risk_factors', [])}")
    print(f"Cart Total: ${signals.get('cart_total', 0):.2f}")
    print(f"Customer Velocity (24h): {signals.get('customer_velocity_24h', 0)}")
    print(f"Customer Chargebacks (12m): {signals.get('customer_chargebacks_12m', 0)}")
    print(f"Loyalty Tier: {signals.get('loyalty_tier', 'NONE')}")
    print(f"Merchant MCC: {signals.get('merchant_mcc', 'N/A')}")


def main():
    """Run CLI demonstrations."""
    print("AltWallet CLI Scoring Demo")
    print("=" * 60)

    # Get paths to example files
    basic_file = Path(__file__).parent / "context_basic.json"
    risky_file = Path(__file__).parent / "context_risky.json"

    # Test 1: Basic context
    print("\n1. Testing Basic Context (Low Risk)")
    result1 = run_cli_score(basic_file, trace_id="demo-basic-123")
    print_scoring_result("BASIC CONTEXT RESULT", result1)

    # Test 2: Risky context
    print("\n2. Testing Risky Context (High Risk)")
    result2 = run_cli_score(risky_file, trace_id="demo-risky-456")
    print_scoring_result("RISKY CONTEXT RESULT", result2)

    # Test 3: Pretty output
    print("\n3. Testing Pretty Output")
    result3 = run_cli_score(basic_file, trace_id="demo-pretty-789", pretty=True)
    print_scoring_result("PRETTY OUTPUT RESULT", result3)

    # Test 4: Stdin input
    print("\n4. Testing Stdin Input")
    with open(basic_file) as f:
        json_input = f.read()

    cmd = [
        sys.executable,
        "-m",
        "altwallet_agent",
        "score",
        "--trace-id",
        "demo-stdin-999",
    ]

    result = subprocess.run(
        cmd,
        input=json_input,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )

    if result.returncode == 0:
        result4 = json.loads(result.stdout.strip())
        print_scoring_result("STDIN INPUT RESULT", result4)
    else:
        print("❌ Stdin test failed")

    # Summary
    print(f"\n{'='*60}")
    print("DEMO SUMMARY")
    print(f"{'='*60}")

    if result1 and result2 and result3:
        print("✅ All CLI tests completed successfully!")
        print(f"Basic Score: {result1['final_score']}")
        print(f"Risky Score: {result2['final_score']}")
        print(f"Score Difference: {result1['final_score'] - result2['final_score']}")
    else:
        print("❌ Some CLI tests failed!")

    print(f"\n{'='*60}")
    print("DEMO COMPLETE")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
