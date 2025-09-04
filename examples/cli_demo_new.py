#!/usr/bin/env python3
"""
CLI Demo Script

Demonstrates the AltWallet Checkout Agent CLI functionality.
"""

import os
import subprocess


def run_cli_command(command):
    """Run a CLI command and display output."""
    print(f"\n🚀 Running: {command}")
    print("=" * 60)

    try:
        result = subprocess.run(
            command.split(),
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(__file__)),
        )

        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"STDERR: {result.stderr}")
        if result.returncode != 0:
            print(f"Command failed with return code: {result.returncode}")

    except Exception as e:
        print(f"Error running command: {e}")


def main():
    """Run CLI demo commands."""
    print("🎯 AltWallet Checkout Agent CLI Demo")
    print("=" * 50)

    # Check if CLI module exists
    cli_path = "src/altwallet_agent/cli.py"
    if not os.path.exists(cli_path):
        print(f"❌ CLI module not found at: {cli_path}")
        return

    print("✅ CLI module found")

    # Demo commands
    commands = [
        "python -m src.altwallet_agent.cli --help",
        "python -m src.altwallet_agent.cli simulate-decision --help",
        "python -m src.altwallet_agent.cli simulate-decision --approve --discount",
        "python -m src.altwallet_agent.cli simulate-decision --decline --kyc",
        "python -m src.altwallet_agent.cli simulate-decision --review --kyc "
        "--webhook --analytics",
        "python -m src.altwallet_agent.cli simulate-decision --approve "
        "--amount 500 --mcc 5814 --webhook --analytics "
        "--output-file decision_output.json",
        "python -m src.altwallet_agent.cli health-check",
        "python -m src.altwallet_agent.cli list-webhooks",
    ]

    for command in commands:
        run_cli_command(command)
        print("\n" + "-" * 60)

    print("\n✨ CLI Demo Complete!")
    print("\n📋 Available Commands:")
    print("  simulate-decision  - Simulate transaction decisions")
    print("  list-webhooks      - List configured webhooks")
    print("  webhook-history    - Check webhook delivery history")
    print("  health-check       - Check system health")


if __name__ == "__main__":
    main()
