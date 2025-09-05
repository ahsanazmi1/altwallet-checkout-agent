"""Example integration of AltWallet Checkout Agent in inline mode.

This example shows how to integrate the AltWallet Checkout Agent directly
into a merchant application using the inline deployment mode.
"""

import asyncio
import json
from typing import Dict, Any, Optional

from deployment import (
    DeploymentConfig,
    InlineConfig,
    InlineCheckoutClient,
    SyncInlineCheckoutClient,
    process_checkout_inline,
    inline_checkout_client,
)
from src.altwallet_agent.models import CheckoutRequest, Context


class MerchantCheckoutApp:
    """Example merchant application with inline AltWallet integration."""
    
    def __init__(self):
        self.checkout_client: Optional[InlineCheckoutClient] = None
        self.initialized = False
    
    async def initialize(self):
        """Initialize the merchant app and AltWallet client."""
        print("🚀 Initializing Merchant Checkout App...")
        
        # Configure inline deployment
        inline_config = InlineConfig(
            merchant_app_name="example-merchant-app",
            integration_method="direct_import",
            cache_enabled=True,
            cache_ttl=300,
            retry_attempts=3,
            circuit_breaker_enabled=True,
            circuit_breaker_threshold=5
        )
        
        # Create inline client
        self.checkout_client = InlineCheckoutClient(inline_config)
        await self.checkout_client.initialize()
        
        self.initialized = True
        print("✅ Merchant app initialized successfully")
    
    async def process_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a payment with AltWallet recommendations."""
        if not self.initialized:
            await self.initialize()
        
        print(f"💳 Processing payment: ${payment_data.get('amount', 0)}")
        
        try:
            # Create checkout request
            checkout_request = CheckoutRequest(
                merchant_id=payment_data.get("merchant_id", "example-merchant"),
                amount=payment_data.get("amount", 100.0),
                currency=payment_data.get("currency", "USD")
            )
            
            # Process with AltWallet
            response = await self.checkout_client.process_checkout(checkout_request)
            
            # Extract recommendations
            recommendations = []
            for rec in response.recommendations:
                recommendations.append({
                    "card_name": rec.card_name,
                    "rank": rec.rank,
                    "approval_probability": rec.p_approval,
                    "expected_rewards": rec.expected_rewards,
                    "utility_score": rec.utility
                })
            
            result = {
                "success": True,
                "transaction_id": response.transaction_id,
                "score": response.score,
                "recommendations": recommendations,
                "best_card": recommendations[0] if recommendations else None
            }
            
            print(f"✅ Payment processed successfully")
            print(f"   Best card: {result['best_card']['card_name'] if result['best_card'] else 'None'}")
            print(f"   Approval probability: {result['best_card']['approval_probability']:.2%}" if result['best_card'] else "")
            
            return result
            
        except Exception as e:
            print(f"❌ Payment processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "transaction_id": None
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        if not self.initialized:
            return {"status": "not_initialized"}
        
        try:
            health = await self.checkout_client.health_check()
            return {
                "status": "healthy",
                "altwallet": health,
                "merchant_app": "running"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        if not self.initialized:
            return {}
        
        return self.checkout_client.get_metrics()
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.checkout_client:
            await self.checkout_client.cleanup()
        print("🧹 Merchant app cleaned up")


class SyncMerchantCheckoutApp:
    """Synchronous version of merchant application."""
    
    def __init__(self):
        self.checkout_client: Optional[SyncInlineCheckoutClient] = None
        self.initialized = False
    
    def initialize(self):
        """Initialize the merchant app and AltWallet client."""
        print("🚀 Initializing Sync Merchant Checkout App...")
        
        # Configure inline deployment
        inline_config = InlineConfig(
            merchant_app_name="sync-merchant-app",
            integration_method="direct_import",
            cache_enabled=True,
            cache_ttl=300,
            retry_attempts=3,
            circuit_breaker_enabled=True,
            circuit_breaker_threshold=5
        )
        
        # Create sync inline client
        self.checkout_client = SyncInlineCheckoutClient(inline_config)
        self.checkout_client.initialize()
        
        self.initialized = True
        print("✅ Sync merchant app initialized successfully")
    
    def process_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a payment with AltWallet recommendations."""
        if not self.initialized:
            self.initialize()
        
        print(f"💳 Processing payment: ${payment_data.get('amount', 0)}")
        
        try:
            # Create checkout request
            checkout_request = CheckoutRequest(
                merchant_id=payment_data.get("merchant_id", "example-merchant"),
                amount=payment_data.get("amount", 100.0),
                currency=payment_data.get("currency", "USD")
            )
            
            # Process with AltWallet
            response = self.checkout_client.process_checkout(checkout_request)
            
            # Extract recommendations
            recommendations = []
            for rec in response.recommendations:
                recommendations.append({
                    "card_name": rec.card_name,
                    "rank": rec.rank,
                    "approval_probability": rec.p_approval,
                    "expected_rewards": rec.expected_rewards,
                    "utility_score": rec.utility
                })
            
            result = {
                "success": True,
                "transaction_id": response.transaction_id,
                "score": response.score,
                "recommendations": recommendations,
                "best_card": recommendations[0] if recommendations else None
            }
            
            print(f"✅ Payment processed successfully")
            print(f"   Best card: {result['best_card']['card_name'] if result['best_card'] else 'None'}")
            print(f"   Approval probability: {result['best_card']['approval_probability']:.2%}" if result['best_card'] else "")
            
            return result
            
        except Exception as e:
            print(f"❌ Payment processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "transaction_id": None
            }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        if not self.initialized:
            return {"status": "not_initialized"}
        
        try:
            health = self.checkout_client.health_check()
            return {
                "status": "healthy",
                "altwallet": health,
                "merchant_app": "running"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        if not self.initialized:
            return {}
        
        return self.checkout_client.get_metrics()
    
    def cleanup(self):
        """Cleanup resources."""
        if self.checkout_client:
            self.checkout_client.cleanup()
        print("🧹 Sync merchant app cleaned up")


async def async_example():
    """Example of async inline integration."""
    print("=== Async Inline Integration Example ===")
    
    app = MerchantCheckoutApp()
    
    try:
        # Initialize
        await app.initialize()
        
        # Process some payments
        payments = [
            {"merchant_id": "grocery-store", "amount": 45.99, "currency": "USD"},
            {"merchant_id": "electronics-store", "amount": 299.99, "currency": "USD"},
            {"merchant_id": "gas-station", "amount": 25.00, "currency": "USD"},
        ]
        
        for payment in payments:
            result = await app.process_payment(payment)
            print(f"Result: {json.dumps(result, indent=2)}\n")
        
        # Health check
        health = await app.health_check()
        print(f"Health: {json.dumps(health, indent=2)}\n")
        
        # Metrics
        metrics = await app.get_metrics()
        print(f"Metrics: {json.dumps(metrics, indent=2)}\n")
        
    finally:
        await app.cleanup()


def sync_example():
    """Example of sync inline integration."""
    print("=== Sync Inline Integration Example ===")
    
    app = SyncMerchantCheckoutApp()
    
    try:
        # Initialize
        app.initialize()
        
        # Process some payments
        payments = [
            {"merchant_id": "grocery-store", "amount": 45.99, "currency": "USD"},
            {"merchant_id": "electronics-store", "amount": 299.99, "currency": "USD"},
            {"merchant_id": "gas-station", "amount": 25.00, "currency": "USD"},
        ]
        
        for payment in payments:
            result = app.process_payment(payment)
            print(f"Result: {json.dumps(result, indent=2)}\n")
        
        # Health check
        health = app.health_check()
        print(f"Health: {json.dumps(health, indent=2)}\n")
        
        # Metrics
        metrics = app.get_metrics()
        print(f"Metrics: {json.dumps(metrics, indent=2)}\n")
        
    finally:
        app.cleanup()


async def context_manager_example():
    """Example using context manager."""
    print("=== Context Manager Example ===")
    
    inline_config = InlineConfig(
        merchant_app_name="context-manager-app",
        cache_enabled=True,
        circuit_breaker_enabled=True
    )
    
    async with inline_checkout_client(inline_config) as client:
        # Process a payment
        request = CheckoutRequest(
            merchant_id="test-merchant",
            amount=100.0,
            currency="USD"
        )
        
        response = await client.process_checkout(request)
        print(f"Context manager result: {response.transaction_id}")


async def convenience_function_example():
    """Example using convenience function."""
    print("=== Convenience Function Example ===")
    
    request = CheckoutRequest(
        merchant_id="convenience-merchant",
        amount=50.0,
        currency="USD"
    )
    
    response = await process_checkout_inline(request)
    print(f"Convenience function result: {response.transaction_id}")


if __name__ == "__main__":
    print("AltWallet Checkout Agent - Inline Integration Examples")
    print("=" * 60)
    
    # Run async example
    asyncio.run(async_example())
    
    print("\n" + "=" * 60)
    
    # Run sync example
    sync_example()
    
    print("\n" + "=" * 60)
    
    # Run context manager example
    asyncio.run(context_manager_example())
    
    print("\n" + "=" * 60)
    
    # Run convenience function example
    asyncio.run(convenience_function_example())
    
    print("\n✅ All examples completed successfully!")
