#!/usr/bin/env python3
"""Demo script showing structured logging with AltWallet Checkout Agent."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from altwallet_agent.logger import get_logger, set_trace_id


def demo_logging():
    """Demonstrate structured logging functionality."""
    print("=== AltWallet Checkout Agent - Structured Logging Demo ===\n")

    # Set log level to INFO to see structured logs
    os.environ["LOG_LEVEL"] = "INFO"

    # Simulate a checkout process with logging
    trace_id = "demo-checkout-456"
    set_trace_id(trace_id)
    logger = get_logger("checkout_demo")

    logger.info(
        "Starting checkout process",
        merchant_id="merchant_123",
        amount=299.99,
        currency="USD",
        user_id="user_456",
    )

    # Simulate context parsing
    logger.info(
        "Context parsed successfully",
        context_keys=["merchant", "customer", "cart", "device"],
    )

    # Simulate scoring
    logger.info("Starting transaction scoring")
    logger.info(
        "Scoring completed",
        final_score=85,
        routing_hint="visa",
        risk_score=15,
        loyalty_boost=10,
    )

    print("\n=== Demo completed ===")
    print("The JSON logs above show structured logging with:")
    print("- ISO8601 timestamps")
    print("- Log levels")
    print("- Trace IDs for correlation")
    print("- Structured event data")


if __name__ == "__main__":
    demo_logging()
