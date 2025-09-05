"""Advanced usage example for the AltWallet Python SDK."""

import asyncio
import json
from typing import List, Dict, Any
from altwallet_sdk import (
    AltWalletClient, 
    SDKConfig, 
    QuoteRequest, 
    Cart, 
    Customer, 
    Context,
    ValidationError,
    NetworkError,
    APIError
)


class MerchantCheckoutService:
    """Example merchant checkout service using AltWallet SDK."""
    
    def __init__(self, config: SDKConfig):
        self.client = AltWalletClient(config)
        self.initialized = False
    
    async def initialize(self):
        """Initialize the service."""
        await self.client.initialize()
        self.initialized = True
        print("✅ Merchant checkout service initialized")
    
    async def process_checkout(
        self, 
        cart_data: Dict[str, Any], 
        customer_data: Dict[str, Any], 
        context_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a checkout with AltWallet recommendations."""
        if not self.initialized:
            await self.initialize()
        
        try:
            # Create request objects
            cart = Cart(**cart_data)
            customer = Customer(**customer_data)
            context = Context(**context_data)
            
            # Get recommendations
            response = await self.client.quote(cart, customer, context)
            
            # Process recommendations
            recommendations = []
            for rec in response.recommendations:
                recommendations.append({
                    "card_id": rec.card_id,
                    "card_name": rec.card_name,
                    "issuer": rec.issuer,
                    "rank": rec.rank,
                    "approval_probability": rec.approval_probability,
                    "expected_rewards": rec.expected_rewards,
                    "utility_score": rec.utility_score,
                    "reasoning": rec.reasoning
                })
            
            return {
                "success": True,
                "transaction_id": response.transaction_id,
                "request_id": response.request_id,
                "score": response.score,
                "recommendations": recommendations,
                "best_card": recommendations[0] if recommendations else None,
                "processing_time_ms": response.processing_time_ms
            }
            
        except ValidationError as e:
            return {
                "success": False,
                "error": "validation_error",
                "message": str(e),
                "details": e.details
            }
        except NetworkError as e:
            return {
                "success": False,
                "error": "network_error",
                "message": str(e)
            }
        except APIError as e:
            return {
                "success": False,
                "error": "api_error",
                "message": str(e),
                "status_code": e.status_code
            }
        except Exception as e:
            return {
                "success": False,
                "error": "unknown_error",
                "message": str(e)
            }
    
    async def get_decision_details(self, request_id: str) -> Dict[str, Any]:
        """Get decision details for a request."""
        try:
            decision = await self.client.decision(request_id)
            return {
                "success": True,
                "decision": decision.decision,
                "confidence": decision.confidence,
                "reasoning": decision.reasoning,
                "risk_factors": decision.risk_factors
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check service health."""
        try:
            health = await self.client.health_check()
            metrics = self.client.get_metrics()
            
            return {
                "status": "healthy",
                "api_health": health,
                "client_metrics": metrics
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def cleanup(self):
        """Cleanup service resources."""
        await self.client.cleanup()
        print("🧹 Merchant checkout service cleaned up")


async def advanced_example():
    """Advanced usage example with error handling and batch processing."""
    print("🚀 AltWallet Python SDK - Advanced Usage Example")
    print("=" * 60)
    
    # Configure SDK with custom settings
    config = SDKConfig(
        api_endpoint="http://localhost:8000",
        timeout=60,
        retry_attempts=5,
        retry_delay=2.0,
        connection_pool_size=20,
        log_level="DEBUG"
    )
    
    # Create merchant service
    service = MerchantCheckoutService(config)
    
    try:
        # Initialize service
        await service.initialize()
        
        # Example checkout scenarios
        scenarios = [
            {
                "name": "Grocery Purchase",
                "cart": {
                    "items": [
                        {
                            "item_id": "grocery_001",
                            "name": "Organic Groceries",
                            "unit_price": 85.50,
                            "quantity": 1,
                            "category": "groceries",
                            "mcc": "5411"
                        }
                    ],
                    "currency": "USD",
                    "total_amount": 85.50
                },
                "customer": {
                    "customer_id": "cust_grocery_001",
                    "loyalty_tier": "GOLD",
                    "preferred_cards": ["amex_gold", "chase_sapphire"]
                },
                "context": {
                    "merchant_id": "organic_grocery_123",
                    "merchant_name": "Organic Grocery Store",
                    "device_type": "mobile",
                    "ip_address": "192.168.1.100"
                }
            },
            {
                "name": "Electronics Purchase",
                "cart": {
                    "items": [
                        {
                            "item_id": "electronics_001",
                            "name": "High-End Laptop",
                            "unit_price": 1299.99,
                            "quantity": 1,
                            "category": "electronics",
                            "mcc": "5732"
                        }
                    ],
                    "currency": "USD",
                    "total_amount": 1299.99
                },
                "customer": {
                    "customer_id": "cust_electronics_001",
                    "loyalty_tier": "SILVER",
                    "preferred_cards": ["chase_freedom", "citi_double_cash"]
                },
                "context": {
                    "merchant_id": "electronics_store_456",
                    "merchant_name": "Electronics Store",
                    "device_type": "desktop",
                    "ip_address": "192.168.1.200"
                }
            },
            {
                "name": "Gas Station",
                "cart": {
                    "items": [
                        {
                            "item_id": "gas_001",
                            "name": "Gasoline",
                            "unit_price": 25.00,
                            "quantity": 1,
                            "category": "gas",
                            "mcc": "5541"
                        }
                    ],
                    "currency": "USD",
                    "total_amount": 25.00
                },
                "customer": {
                    "customer_id": "cust_gas_001",
                    "loyalty_tier": "BRONZE",
                    "preferred_cards": ["chase_freedom_unlimited"]
                },
                "context": {
                    "merchant_id": "gas_station_789",
                    "merchant_name": "Local Gas Station",
                    "device_type": "mobile",
                    "ip_address": "192.168.1.300"
                }
            }
        ]
        
        # Process each scenario
        results = []
        for scenario in scenarios:
            print(f"\n🛒 Processing: {scenario['name']}")
            print("-" * 40)
            
            result = await service.process_checkout(
                scenario["cart"],
                scenario["customer"],
                scenario["context"]
            )
            
            results.append({
                "scenario": scenario["name"],
                "result": result
            })
            
            if result["success"]:
                print(f"✅ Success! Transaction ID: {result['transaction_id']}")
                print(f"📊 Score: {result['score']:.2f}")
                if result["best_card"]:
                    best = result["best_card"]
                    print(f"🎯 Best Card: {best['card_name']}")
                    print(f"   Approval: {best['approval_probability']:.1%}")
                    print(f"   Rewards: {best['expected_rewards']:.1%}")
                
                # Get decision details
                decision = await service.get_decision_details(result["request_id"])
                if decision["success"]:
                    print(f"🔍 Decision: {decision['decision']} (Confidence: {decision['confidence']:.1%})")
            else:
                print(f"❌ Failed: {result['message']}")
        
        # Summary
        print("\n📊 Summary")
        print("=" * 30)
        successful = sum(1 for r in results if r["result"]["success"])
        total = len(results)
        print(f"Successful: {successful}/{total}")
        
        # Health check
        print("\n🏥 Service Health Check")
        print("-" * 30)
        health = await service.health_check()
        print(f"Status: {health['status']}")
        if health['status'] == 'healthy':
            metrics = health['client_metrics']
            print(f"Requests: {metrics['request_count']}")
            print(f"Error Rate: {metrics['error_rate']:.1%}")
            print(f"Avg Latency: {metrics['average_latency_ms']:.1f}ms")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    finally:
        await service.cleanup()


async def batch_processing_example():
    """Example of batch processing multiple requests."""
    print("\n🔄 Batch Processing Example")
    print("=" * 40)
    
    config = SDKConfig(
        api_endpoint="http://localhost:8000",
        connection_pool_size=50,  # Higher for batch processing
        timeout=120
    )
    
    service = MerchantCheckoutService(config)
    await service.initialize()
    
    try:
        # Create multiple requests
        requests = []
        for i in range(5):
            requests.append({
                "cart": {
                    "items": [
                        {
                            "item_id": f"item_{i:03d}",
                            "name": f"Product {i}",
                            "unit_price": 10.0 + i * 5,
                            "quantity": 1,
                            "category": "general"
                        }
                    ],
                    "currency": "USD",
                    "total_amount": 10.0 + i * 5
                },
                "customer": {
                    "customer_id": f"cust_{i:03d}",
                    "loyalty_tier": "SILVER"
                },
                "context": {
                    "merchant_id": f"merchant_{i:03d}",
                    "device_type": "mobile"
                }
            })
        
        # Process requests concurrently
        print(f"🚀 Processing {len(requests)} requests concurrently...")
        tasks = [
            service.process_checkout(req["cart"], req["customer"], req["context"])
            for req in requests
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        successful = 0
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Request {i}: ❌ Error - {result}")
            elif result["success"]:
                successful += 1
                print(f"Request {i}: ✅ Success - Score: {result['score']:.2f}")
            else:
                print(f"Request {i}: ❌ Failed - {result['message']}")
        
        print(f"\n📊 Batch Results: {successful}/{len(requests)} successful")
        
    finally:
        await service.cleanup()


if __name__ == "__main__":
    asyncio.run(advanced_example())
    asyncio.run(batch_processing_example())
