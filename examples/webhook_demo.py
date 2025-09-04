#!/usr/bin/env python3
"""Demo script for the AltWallet Checkout Agent Webhook Module.

This script demonstrates how to use the webhook module to send downstream
events with retry logic, exponential backoff, and signed payloads.
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import after path setup
from altwallet_agent.logger import configure_logging
from altwallet_agent.webhooks import (
    WebhookConfig,
    WebhookEventType,
    get_webhook_emitter,
    get_webhook_manager,
    shutdown_webhooks,
)


async def demonstrate_webhooks():
    """Demonstrate the webhook module functionality."""

    print("🚀 AltWallet Checkout Agent - Webhook Module Demo")
    print("=" * 60)

    # Configure logging
    configure_logging()

    # Get webhook manager
    webhook_manager = await get_webhook_manager()

    # Test 1: Add webhook configurations
    print("\n📋 Test 1: Adding Webhook Configurations")
    print("-" * 50)

    # Add webhook for auth results
    auth_webhook = WebhookConfig(
        url="https://webhook.site/your-auth-webhook-url",
        secret="auth_secret_123",
        event_types=[WebhookEventType.AUTH_RESULT],
        timeout=30,
        max_retries=3,
        retry_delay_base=1.0,
        retry_delay_max=60.0,
    )

    await webhook_manager.add_webhook("auth_webhook", auth_webhook)
    print("✅ Auth webhook added")

    # Add webhook for all events
    general_webhook = WebhookConfig(
        url="https://webhook.site/your-general-webhook-url",
        secret="general_secret_456",
        event_types=[],  # Empty list means all event types
        timeout=45,
        max_retries=5,
        retry_delay_base=2.0,
        retry_delay_max=120.0,
    )

    await webhook_manager.add_webhook("general_webhook", general_webhook)
    print("✅ General webhook added")

    # List webhooks
    webhooks = await webhook_manager.list_webhooks()
    print(f"\nConfigured webhooks: {len(webhooks)}")
    for webhook in webhooks:
        print(f"  • {webhook['webhook_id']}: {webhook['url']}")
        print(f"    Event types: {webhook['event_types']}")
        print(f"    Max retries: {webhook['max_retries']}")

    # Test 2: Get webhook event emitter
    print("\n📋 Test 2: Getting Webhook Event Emitter")
    print("-" * 50)

    emitter = await get_webhook_emitter()
    print("✅ Webhook event emitter obtained")

    # Test 3: Emit various events
    print("\n📋 Test 3: Emitting Webhook Events")
    print("-" * 50)

    # Emit auth result event
    print("Emitting auth result event...")
    auth_deliveries = await emitter.emit_auth_result(
        transaction_id="txn_webhook_001",
        decision="APPROVE",
        score=85.0,
        metadata={
            "merchant_id": "merchant_123",
            "customer_id": "customer_456",
            "amount": 150.00,
        },
    )
    print(f"✅ Auth result event emitted to {len(auth_deliveries)} webhooks")

    # Emit settlement event
    print("Emitting settlement event...")
    settlement_deliveries = await emitter.emit_settlement(
        transaction_id="txn_webhook_001",
        amount=150.00,
        currency="USD",
        status="completed",
        metadata={"settlement_id": "settlement_789", "processing_time_ms": 1250},
    )
    print(f"✅ Settlement event emitted to {len(settlement_deliveries)} webhooks")

    # Emit chargeback event
    print("Emitting chargeback event...")
    chargeback_deliveries = await emitter.emit_chargeback(
        transaction_id="txn_webhook_001",
        chargeback_id="cb_webhook_001",
        reason="fraud_suspected",
        amount=150.00,
        metadata={"chargeback_date": "2025-01-15", "reason_code": "10.1"},
    )
    print(f"✅ Chargeback event emitted to {len(chargeback_deliveries)} webhooks")

    # Emit loyalty event
    print("Emitting loyalty event...")
    loyalty_deliveries = await emitter.emit_loyalty_event(
        customer_id="customer_456",
        event_type="points_earned",
        points_change=15,
        metadata={"transaction_amount": 150.00, "points_rate": 0.1, "tier": "SILVER"},
    )
    print(f"✅ Loyalty event emitted to {len(loyalty_deliveries)} webhooks")

    # Test 4: Check delivery history
    print("\n📋 Test 4: Checking Delivery History")
    print("-" * 50)

    # Wait a moment for async operations
    await asyncio.sleep(1)

    # Get delivery history
    all_deliveries = await webhook_manager.get_delivery_history(limit=50)
    print(f"Total deliveries: {len(all_deliveries)}")

    # Group by status
    status_counts = {}
    for delivery in all_deliveries:
        status = delivery.status.value
        status_counts[status] = status_counts.get(status, 0) + 1

    print("Delivery status counts:")
    for status, count in status_counts.items():
        print(f"  • {status}: {count}")

    # Test 5: Webhook management operations
    print("\n📋 Test 5: Webhook Management Operations")
    print("-" * 50)

    # Get specific webhook
    auth_webhook_config = await webhook_manager.get_webhook("auth_webhook")
    if auth_webhook_config:
        print(f"✅ Retrieved auth webhook: {auth_webhook_config.url}")
        print(f"   Event types: {[et.value for et in auth_webhook_config.event_types]}")
        print(f"   Max retries: {auth_webhook_config.max_retries}")
        print(f"   Enabled: {auth_webhook_config.enabled}")

    # Test 6: Cleanup and shutdown
    print("\n📋 Test 6: Cleanup and Shutdown")
    print("-" * 50)

    # Remove a webhook
    await webhook_manager.remove_webhook("auth_webhook")
    print("✅ Auth webhook removed")

    # List remaining webhooks
    remaining_webhooks = await webhook_manager.list_webhooks()
    print(f"Remaining webhooks: {len(remaining_webhooks)}")

    # Shutdown webhook manager
    await shutdown_webhooks()
    print("✅ Webhook manager shut down")

    print("\n✅ Webhook module demo completed successfully!")


async def main():
    """Main function to run the demo."""
    try:
        await demonstrate_webhooks()
    except Exception as e:
        print(f"❌ Error running demo: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
