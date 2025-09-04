#!/usr/bin/env python3
"""
Simple CLI Test Script

Tests basic CLI functionality without complex Context requirements.
"""

import os
import subprocess
import sys


def test_cli_help():
    """Test CLI help command."""
    print("🧪 Testing CLI help command...")

    try:
        result = subprocess.run(
            ["python", "-m", "src.altwallet_agent.cli", "--help"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(__file__)),
        )

        if result.returncode == 0:
            print("✅ CLI help command works")
            return True
        else:
            print(f"❌ CLI help command failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Error testing CLI help: {e}")
        return False


def test_simulate_decision_help():
    """Test simulate-decision help command."""
    print("🧪 Testing simulate-decision help command...")

    try:
        result = subprocess.run(
            ["python", "-m", "src.altwallet_agent.cli", "simulate-decision", "--help"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(__file__)),
        )

        if result.returncode == 0:
            print("✅ simulate-decision help command works")
            return True
        else:
            print(f"❌ simulate-decision help command failed: " f"{result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Error testing simulate-decision help: {e}")
        return False


def test_health_check():
    """Test health-check command."""
    print("🧪 Testing health-check command...")

    try:
        result = subprocess.run(
            ["python", "-m", "src.altwallet_agent.cli", "health-check"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(__file__)),
        )

        if result.returncode == 0:
            print("✅ health-check command works")
            print(f"Output: {result.stdout}")
            return True
        else:
            print(f"❌ health-check command failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Error testing health-check: {e}")
        return False


def test_list_webhooks():
    """Test list-webhooks command."""
    print("🧪 Testing list-webhooks command...")

    try:
        result = subprocess.run(
            ["python", "-m", "src.altwallet_agent.cli", "list-webhooks"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(__file__)),
        )

        if result.returncode == 0:
            print("✅ list-webhooks command works")
            print(f"Output: {result.stdout}")
            return True
        else:
            print(f"❌ list-webhooks command failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Error testing list-webhooks: {e}")
        return False


def main():
    """Run CLI tests."""
    print("🎯 AltWallet Checkout Agent CLI Tests")
    print("=" * 50)

    tests = [
        test_cli_help,
        test_simulate_decision_help,
        test_health_check,
        test_list_webhooks,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print("📊 Test Results:")
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("🎉 All CLI tests passed!")
    else:
        print("❌ Some CLI tests failed!")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
