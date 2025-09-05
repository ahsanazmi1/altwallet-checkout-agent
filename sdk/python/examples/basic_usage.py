"""Basic usage example for the AltWallet Python SDK."""

import asyncio

from altwallet_sdk import (
    AltWalletClient,
    Cart,
    Context,
    Customer,
    SDKConfig,
)


async def main():
    """Basic usage example."""
    print("🚀 AltWallet Python SDK - Basic Usage Example")
    print("=" * 50)

    # Configure the SDK
    config = SDKConfig(
        api_endpoint="http://localhost:8000",
        api_key="your-api-key-here",  # Optional
        timeout=30,
        retry_attempts=3,
        log_level="INFO",
    )

    # Create client
    client = AltWalletClient(config)

    try:
        # Initialize the client
        print("📡 Initializing client...")
        await client.initialize()
        print("✅ Client initialized successfully")

        # Prepare request data
        cart = Cart(
            items=[
                {
                    "item_id": "item_123",
                    "name": "Grocery Items",
                    "unit_price": 45.99,
                    "quantity": 1,
                    "category": "groceries",
                    "mcc": "5411",
                }
            ],
            currency="USD",
            total_amount=45.99,
        )

        customer = Customer(
            customer_id="cust_12345",
            loyalty_tier="SILVER",
            preferred_cards=["amex_gold", "chase_freedom"],
        )

        context = Context(
            merchant_id="grocery_store_123",
            merchant_name="Local Grocery Store",
            device_type="mobile",
            ip_address="192.168.1.100",
        )

        # Get card recommendations
        print("\n💳 Getting card recommendations...")
        response = await client.quote(cart, customer, context)

        print(f"✅ Received {len(response.recommendations)} recommendations")
        print(f"📊 Transaction Score: {response.score:.2f}")
        print(f"⏱️  Processing Time: {response.processing_time_ms}ms")

        # Display recommendations
        print("\n🎯 Top Recommendations:")
        for i, rec in enumerate(response.recommendations[:3], 1):
            print(f"{i}. {rec.card_name} ({rec.issuer})")
            print(f"   Approval Probability: {rec.approval_probability:.1%}")
            print(f"   Expected Rewards: {rec.expected_rewards:.1%}")
            print(f"   Utility Score: {rec.utility_score:.2f}")
            if rec.reasoning:
                print(f"   Reasoning: {rec.reasoning}")
            print()

        # Get decision details
        print("🔍 Getting decision details...")
        decision = await client.decision(response.request_id)

        print(f"✅ Decision: {decision.decision}")
        print(f"🎯 Confidence: {decision.confidence:.1%}")
        print(f"💭 Reasoning: {decision.reasoning}")

        # Health check
        print("\n🏥 Checking API health...")
        health = await client.health_check()
        print(f"Status: {health.get('status', 'unknown')}")

        # Get metrics
        print("\n📈 Client Metrics:")
        metrics = client.get_metrics()
        print(f"Requests: {metrics['request_count']}")
        print(f"Errors: {metrics['error_count']}")
        print(f"Error Rate: {metrics['error_rate']:.1%}")
        print(f"Avg Latency: {metrics['average_latency_ms']:.1f}ms")

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        # Cleanup
        await client.cleanup()
        print("\n🧹 Client cleaned up")


if __name__ == "__main__":
    asyncio.run(main())
