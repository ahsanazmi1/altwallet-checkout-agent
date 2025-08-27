#!/usr/bin/env python3
"""Demo script for the ApprovalScorer module."""

from decimal import Decimal

from altwallet_agent.approval_scorer import ApprovalScorer


def main():
    """Demonstrate the ApprovalScorer functionality."""
    print("=== AltWallet ApprovalScorer Demo ===\n")
    
    # Initialize the scorer
    scorer = ApprovalScorer()
    print("✓ ApprovalScorer initialized with default configuration\n")
    
    # Example 1: Low-risk transaction
    print("Example 1: Low-risk transaction")
    print("-" * 40)
    low_risk_context = {
        "mcc": "5411",  # Grocery store
        "amount": Decimal("25.00"),
        "issuer_family": "visa",
        "cross_border": False,
        "location_mismatch_distance": 0.0,
        "velocity_24h": 2,
        "velocity_7d": 8,
        "chargebacks_12m": 0,
        "merchant_risk_tier": "low",
        "loyalty_tier": "PLATINUM"
    }
    
    result = scorer.score(low_risk_context)
    print(f"Approval Probability: {result.p_approval:.3f}")
    print(f"Raw Score: {result.raw_score:.3f}")
    print(f"Calibration Method: {result.calibration['method']}")
    print()
    
    # Example 2: High-risk transaction
    print("Example 2: High-risk transaction")
    print("-" * 40)
    high_risk_context = {
        "mcc": "7995",  # Gambling
        "amount": Decimal("2000.00"),
        "issuer_family": "unknown",
        "cross_border": True,
        "location_mismatch_distance": 200.0,
        "velocity_24h": 25,
        "velocity_7d": 150,
        "chargebacks_12m": 3,
        "merchant_risk_tier": "high",
        "loyalty_tier": "NONE"
    }
    
    result = scorer.score(high_risk_context)
    print(f"Approval Probability: {result.p_approval:.3f}")
    print(f"Raw Score: {result.raw_score:.3f}")
    print(f"Calibration Method: {result.calibration['method']}")
    print()
    
    # Example 3: Medium-risk transaction
    print("Example 3: Medium-risk transaction")
    print("-" * 40)
    medium_risk_context = {
        "mcc": "5541",  # Gas station
        "amount": Decimal("500.00"),
        "issuer_family": "mastercard",
        "cross_border": False,
        "location_mismatch_distance": 50.0,
        "velocity_24h": 8,
        "velocity_7d": 35,
        "chargebacks_12m": 1,
        "merchant_risk_tier": "medium",
        "loyalty_tier": "SILVER"
    }
    
    result = scorer.score(medium_risk_context)
    print(f"Approval Probability: {result.p_approval:.3f}")
    print(f"Raw Score: {result.raw_score:.3f}")
    print(f"Calibration Method: {result.calibration['method']}")
    print()
    
    # Example 4: Missing fields (should use defaults)
    print("Example 4: Transaction with missing fields")
    print("-" * 40)
    minimal_context = {
        "amount": Decimal("100.00")
        # All other fields missing
    }
    
    result = scorer.score(minimal_context)
    print(f"Approval Probability: {result.p_approval:.3f}")
    print(f"Raw Score: {result.raw_score:.3f}")
    print(f"Calibration Method: {result.calibration['method']}")
    print()
    
    # Example 5: Feature attributions
    print("Example 5: Feature attributions for low-risk transaction")
    print("-" * 40)
    attributions = scorer.explain(low_risk_context)
    print("Feature Contributions:")
    print(f"  MCC: {attributions.mcc_contribution:+.3f}")
    print(f"  Amount: {attributions.amount_contribution:+.3f}")
    print(f"  Issuer: {attributions.issuer_contribution:+.3f}")
    print(f"  Cross-border: {attributions.cross_border_contribution:+.3f}")
    print(f"  Location mismatch: {attributions.location_mismatch_contribution:+.3f}")
    print(f"  Velocity (24h): {attributions.velocity_24h_contribution:+.3f}")
    print(f"  Velocity (7d): {attributions.velocity_7d_contribution:+.3f}")
    print(f"  Chargebacks: {attributions.chargeback_contribution:+.3f}")
    print(f"  Merchant risk: {attributions.merchant_risk_contribution:+.3f}")
    print(f"  Loyalty: {attributions.loyalty_contribution:+.3f}")
    print(f"  Base score: {attributions.base_contribution:+.3f}")
    total = (attributions.mcc_contribution + attributions.amount_contribution + 
             attributions.issuer_contribution + attributions.cross_border_contribution + 
             attributions.location_mismatch_contribution + attributions.velocity_24h_contribution + 
             attributions.velocity_7d_contribution + attributions.chargeback_contribution + 
             attributions.merchant_risk_contribution + attributions.loyalty_contribution + 
             attributions.base_contribution)
    print(f"  Total: {total:+.3f}")
    print()
    
    # Example 6: Deterministic behavior
    print("Example 6: Deterministic behavior test")
    print("-" * 40)
    test_context = {
        "mcc": "5411",
        "amount": Decimal("100.00"),
        "issuer_family": "visa",
        "cross_border": False,
        "location_mismatch_distance": 0.0,
        "velocity_24h": 5,
        "velocity_7d": 20,
        "chargebacks_12m": 0,
        "merchant_risk_tier": "medium",
        "loyalty_tier": "SILVER"
    }
    
    result1 = scorer.score(test_context)
    result2 = scorer.score(test_context)
    
    print(f"First run - Approval Probability: {result1.p_approval:.6f}")
    print(f"Second run - Approval Probability: {result2.p_approval:.6f}")
    print(f"Results identical: {result1.p_approval == result2.p_approval}")
    print()
    
    print("=== Demo completed successfully! ===")


if __name__ == "__main__":
    main()
