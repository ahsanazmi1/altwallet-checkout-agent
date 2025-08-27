#!/usr/bin/env python3
"""Demo script for Enhanced Recommendations with Explainability and Audit."""

import json
from decimal import Decimal

from altwallet_agent.core import CheckoutAgent
from altwallet_agent.models import CheckoutRequest


def main():
    """Demonstrate the enhanced recommendations functionality."""
    print("=== AltWallet Enhanced Recommendations Demo ===\n")
    
    # Initialize the agent
    agent = CheckoutAgent()
    print("✓ CheckoutAgent initialized\n")
    
    # Create a sample checkout request
    request = CheckoutRequest(
        merchant_id="demo_merchant_123",
        amount=Decimal("150.00"),
        currency="USD",
        cart={
            "items": [
                {
                    "item": "Grocery Shopping",
                    "unit_price": "150.00",
                    "qty": 1,
                    "mcc": "5411"
                }
            ],
            "currency": "USD"
        },
        merchant={
            "name": "Demo Grocery Store",
            "mcc": "5411",
            "network_preferences": ["visa", "mastercard"],
            "location": {
                "city": "New York",
                "country": "US"
            }
        },
        customer={
            "id": "customer_456",
            "loyalty_tier": "GOLD",
            "historical_velocity_24h": 3,
            "chargebacks_12m": 0
        },
        device={
            "ip": "192.168.1.100",
            "device_id": "device_789",
            "location": {
                "city": "New York",
                "country": "US"
            }
        },
        geo={
            "city": "New York",
            "country": "US"
        }
    )
    
    print("Processing enhanced checkout request...")
    print(f"Amount: ${request.amount}")
    print(f"Merchant: {request.merchant['name']} ({request.merchant['mcc']})")
    print(f"Customer: {request.customer['id']} ({request.customer['loyalty_tier']})")
    print()
    
    # Process the request with enhanced recommendations
    response = agent.process_checkout_enhanced(request)
    
    print("=== Enhanced Response ===")
    print(f"Transaction ID: {response.transaction_id}")
    print(f"Overall Score: {response.score:.3f}")
    print(f"Status: {response.status}")
    print(f"Processing Time: {response.metadata['processing_time_ms']}ms")
    print()
    
    # Display recommendations
    print("=== Card Recommendations ===")
    for i, rec in enumerate(response.recommendations, 1):
        print(f"\n{i}. {rec.card_name} (Rank: {rec.rank})")
        print(f"   Card ID: {rec.card_id}")
        print(f"   Approval Probability: {rec.p_approval:.3f}")
        print(f"   Expected Rewards: {rec.expected_rewards:.3f}")
        print(f"   Utility Score: {rec.utility:.3f}")
        
        # Display explainability
        print("   Explainability:")
        print(f"     Baseline: {rec.explainability['baseline']:.3f}")
        
        # Show top drivers
        if rec.explainability['top_drivers']['positive']:
            print("     Top Positive Drivers:")
            for driver in rec.explainability['top_drivers']['positive']:
                print(f"       - {driver['feature']}: +{driver['value']:.3f}")
        
        if rec.explainability['top_drivers']['negative']:
            print("     Top Negative Drivers:")
            for driver in rec.explainability['top_drivers']['negative']:
                print(f"       - {driver['feature']}: {driver['value']:.3f}")
        
        # Display audit info
        print("   Audit Info:")
        print(f"     Request ID: {rec.audit['request_id']}")
        print(f"     Code Version: {rec.audit['code_version']}")
        print(f"     Latency: {rec.audit['latency_ms']}ms")
        print(f"     Config Versions: {rec.audit['config_versions']}")
    
    print("\n=== JSON Output ===")
    # Convert to JSON for demonstration
    json_output = response.model_dump()
    print(json.dumps(json_output, indent=2, default=str))
    
    print("\n=== Compact JSON (for API) ===")
    # Create a more compact version for API responses
    compact_response = {
        "transaction_id": response.transaction_id,
        "score": response.score,
        "status": response.status,
        "recommendations": []
    }
    
    for rec in response.recommendations:
        compact_rec = {
            "card_id": rec.card_id,
            "card_name": rec.card_name,
            "rank": rec.rank,
            "p_approval": rec.p_approval,
            "expected_rewards": rec.expected_rewards,
            "utility": rec.utility,
            "explainability": {
                "baseline": rec.explainability["baseline"],
                "contributions": rec.explainability["contributions"],
                "top_drivers": rec.explainability["top_drivers"]
            },
            "audit": {
                "request_id": rec.audit["request_id"],
                "code_version": rec.audit["code_version"],
                "latency_ms": rec.audit["latency_ms"]
            }
        }
        compact_response["recommendations"].append(compact_rec)
    
    print(json.dumps(compact_response, indent=2, default=str))
    
    print("\n=== Summary ===")
    print(f"Generated {len(response.recommendations)} recommendations")
    print(f"Best card: {response.recommendations[0].card_name}")
    print(f"Best approval probability: {response.recommendations[0].p_approval:.3f}")
    print(
        f"Best expected rewards: {response.recommendations[0].expected_rewards:.3f}"
    )
    print(f"Best utility score: {response.recommendations[0].utility:.3f}")


if __name__ == "__main__":
    main()
