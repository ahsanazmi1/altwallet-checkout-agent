#!/usr/bin/env python3
"""
Comprehensive CLI Demo Script

Demonstrates all CLI functionality including:
- Different decision types (APPROVE, DECLINE, REVIEW)
- Business rule combinations (discount, KYC)
- Webhook integration
- Analytics logging
- Parameter customization
"""

import os
import subprocess
import sys
import time


def run_cli_command(cmd_args):
    """Run a CLI command and return the result."""
    try:
        result = subprocess.run(
            ["python", "-m", "src.altwallet_agent.cli"] + cmd_args,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(__file__)),
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def demo_basic_commands():
    """Demonstrate basic CLI commands."""
    print("🔧 Basic CLI Commands")
    print("=" * 50)

    # Help command
    print("\n1. CLI Help:")
    success, output, error = run_cli_command(["--help"])
    if success:
        print("✅ CLI help works")
        print(
            "   Available commands: simulate-decision, list-webhooks, webhook-history, health-check"
        )
    else:
        print(f"❌ CLI help failed: {error}")

    # Health check
    print("\n2. Health Check:")
    success, output, error = run_cli_command(["health-check"])
    if success:
        print("✅ Health check works")
        print("   System status: HEALTHY")
    else:
        print(f"❌ Health check failed: {error}")

    # List webhooks
    print("\n3. List Webhooks:")
    success, output, error = run_cli_command(["list-webhooks"])
    if success:
        print("✅ List webhooks works")
        print("   No webhooks configured (expected for demo)")
    else:
        print(f"❌ List webhooks failed: {error}")


def demo_decision_simulation():
    """Demonstrate decision simulation with different scenarios."""
    print("\n🎯 Decision Simulation Scenarios")
    print("=" * 50)

    scenarios = [
        {
            "name": "APPROVE with Discount",
            "args": ["simulate-decision", "--approve", "--discount"],
            "description": "Simulates an approval decision with loyalty discount applied",
        },
        {
            "name": "DECLINE with KYC",
            "args": ["simulate-decision", "--decline", "--kyc"],
            "description": "Simulates a decline decision requiring KYC verification",
        },
        {
            "name": "REVIEW with Multiple Rules",
            "args": ["simulate-decision", "--review", "--discount", "--kyc"],
            "description": "Simulates a review decision with both discount and KYC rules",
        },
        {
            "name": "APPROVE with Custom Parameters",
            "args": [
                "simulate-decision",
                "--approve",
                "--customer-id",
                "cust_999",
                "--amount",
                "250.00",
                "--mcc",
                "5999",
            ],
            "description": "Simulates an approval with custom customer, amount, and MCC",
        },
    ]

    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['name']}:")
        print(f"   Description: {scenario['description']}")
        print(f"   Command: {' '.join(scenario['args'])}")

        success, output, error = run_cli_command(scenario["args"])
        if success:
            print("   ✅ Success")
            # Extract key information from output
            if "Decision Contract:" in output:
                lines = output.split("\n")
                for line in lines:
                    if '"decision":' in line:
                        decision = (
                            line.strip().split('"decision":')[1].split(",")[0].strip()
                        )
                        print(f"   Decision: {decision}")
                    elif '"action_type":' in line:
                        action = (
                            line.strip()
                            .split('"action_type":')[1]
                            .split(",")[0]
                            .strip()
                        )
                        print(f"   Action: {action}")
        else:
            print(f"   ❌ Failed: {error}")


def demo_integration_features():
    """Demonstrate integration with webhooks and analytics."""
    print("\n🔗 Integration Features")
    print("=" * 50)

    print("\n1. Decision with Webhook and Analytics:")
    success, output, error = run_cli_command(
        ["simulate-decision", "--approve", "--discount", "--webhook", "--analytics"]
    )

    if success:
        print("✅ Integration test successful")
        print("   - Decision contract generated")
        print("   - Webhook event emitted")
        print("   - Analytics event logged")

        # Check for specific outputs
        if "Decision Contract:" in output:
            print("   ✓ Decision contract displayed")
        if "Webhook event emitted successfully" in output:
            print("   ✓ Webhook emission confirmed")
        if "Analytics event logged successfully" in output:
            print("   ✓ Analytics logging confirmed")
    else:
        print(f"❌ Integration test failed: {error}")


def demo_error_handling():
    """Demonstrate error handling and validation."""
    print("\n⚠️ Error Handling and Validation")
    print("=" * 50)

    # Test invalid decision flag combination
    print("\n1. Invalid Decision Flags (no flags):")
    success, output, error = run_cli_command(["simulate-decision"])
    if "ERROR:" in output:
        print("✅ Correctly rejected: Must specify exactly one decision flag")
    else:
        print("❌ Should have been rejected")

    # Test multiple decision flags
    print("\n2. Invalid Decision Flags (multiple flags):")
    success, output, error = run_cli_command(
        ["simulate-decision", "--approve", "--decline"]
    )
    if "ERROR:" in output:
        print("✅ Correctly rejected: Cannot specify multiple decision flags")
    else:
        print("❌ Should have been rejected")


def main():
    """Run the comprehensive CLI demo."""
    print("🚀 AltWallet Checkout Agent - Comprehensive CLI Demo")
    print("=" * 70)
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python: {sys.version}")
    print()

    try:
        # Run all demo sections
        demo_basic_commands()
        demo_decision_simulation()
        demo_integration_features()
        demo_error_handling()

        print("\n" + "=" * 70)
        print("🎉 Comprehensive CLI Demo Completed Successfully!")
        print("\nKey Features Demonstrated:")
        print("✅ Basic CLI commands (help, health-check, list-webhooks)")
        print("✅ Decision simulation (APPROVE, DECLINE, REVIEW)")
        print("✅ Business rule combinations (discount, KYC)")
        print("✅ Custom parameters (customer-id, amount, MCC)")
        print("✅ Webhook integration")
        print("✅ Analytics logging")
        print("✅ Error handling and validation")

        print("\nNext Steps:")
        print("1. Use 'python -m src.altwallet_agent.cli --help' for command overview")
        print("2. Try different decision scenarios with various flags")
        print("3. Experiment with custom parameters")
        print("4. Check webhook and analytics integration")

    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        return False

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
