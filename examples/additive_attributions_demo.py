#!/usr/bin/env python3
"""Demo script for Additive Feature Attributions."""

from decimal import Decimal

from altwallet_agent.approval_scorer import ApprovalScorer


def main():
    """Demonstrate the additive feature attributions functionality."""
    print("=== AltWallet Additive Feature Attributions Demo ===\n")

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
        "loyalty_tier": "PLATINUM",
    }

    result = scorer.score(low_risk_context)
    additive_attribs = scorer.explain(low_risk_context)

    print(f"Approval Probability: {result.p_approval:.3f}")
    print(f"Raw Score: {result.raw_score:.3f}")
    print(f"Baseline: {additive_attribs.baseline:.3f}")
    print(f"Total Contributions: {len(additive_attribs.contribs)}")
    print()

    print("Feature Contributions:")
    for contrib in additive_attribs.contribs:
        sign = "+" if contrib.value >= 0 else ""
        print(f"  {contrib.feature}: {sign}{contrib.value:.3f}")

    print(f"\nSum Validation: {additive_attribs.sum:.3f}")
    print(f"Raw Score Match: {result.raw_score:.3f}")
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
        "loyalty_tier": "NONE",
    }

    result = scorer.score(high_risk_context)
    additive_attribs = scorer.explain(high_risk_context)

    print(f"Approval Probability: {result.p_approval:.3f}")
    print(f"Raw Score: {result.raw_score:.3f}")
    print(f"Baseline: {additive_attribs.baseline:.3f}")
    print(f"Total Contributions: {len(additive_attribs.contribs)}")
    print()

    print("Feature Contributions:")
    for contrib in additive_attribs.contribs:
        sign = "+" if contrib.value >= 0 else ""
        print(f"  {contrib.feature}: {sign}{contrib.value:.3f}")

    print(f"\nSum Validation: {additive_attribs.sum:.3f}")
    print(f"Raw Score Match: {result.raw_score:.3f}")
    print()

    # Example 3: Top drivers extraction
    print("Example 3: Top drivers extraction")
    print("-" * 40)

    # Extract top drivers for high-risk transaction
    top_drivers = scorer._extract_top_drivers(additive_attribs, top_k=3)

    print("Top Positive Drivers:")
    for i, contrib in enumerate(top_drivers["top_positive"], 1):
        print(f"  {i}. {contrib.feature}: +{contrib.value:.3f}")

    print("\nTop Negative Drivers:")
    for i, contrib in enumerate(top_drivers["top_negative"], 1):
        print(f"  {i}. {contrib.feature}: {contrib.value:.3f}")
    print()

    # Example 4: JSON serialization
    print("Example 4: JSON serialization")
    print("-" * 40)

    import json

    json_str = json.dumps(additive_attribs.model_dump(), indent=2)
    print("Additive Attributions JSON:")
    print(json_str)
    print()

    # Example 5: Additivity validation
    print("Example 5: Additivity validation")
    print("-" * 40)

    contrib_sum = sum(contrib.value for contrib in additive_attribs.contribs)
    total_sum = contrib_sum + additive_attribs.baseline

    print(f"Sum of contributions: {contrib_sum:.6f}")
    print(f"Baseline: {additive_attribs.baseline:.6f}")
    print(f"Total sum: {total_sum:.6f}")
    print(f"Attributions sum: {additive_attribs.sum:.6f}")
    print(f"Raw score: {result.raw_score:.6f}")

    epsilon = 1e-10
    if abs(total_sum - additive_attribs.sum) <= epsilon:
        print("✓ Additivity validation passed")
    else:
        print("✗ Additivity validation failed")

    if abs(total_sum - result.raw_score) <= epsilon:
        print("✓ Raw score match validation passed")
    else:
        print("✗ Raw score match validation failed")
    print()

    # Example 6: Comparison between low and high risk
    print("Example 6: Low vs High Risk Comparison")
    print("-" * 40)

    low_risk_attribs = scorer.explain(low_risk_context)

    print("Low Risk Transaction:")
    print(f"  Raw Score: {low_risk_attribs.sum:.3f}")
    pos_count = sum(1 for c in low_risk_attribs.contribs if c.value > 0)
    neg_count = sum(1 for c in low_risk_attribs.contribs if c.value < 0)
    print(f"  Positive contributions: {pos_count}")
    print(f"  Negative contributions: {neg_count}")

    print("\nHigh Risk Transaction:")
    print(f"  Raw Score: {additive_attribs.sum:.3f}")
    pos_count = sum(1 for c in additive_attribs.contribs if c.value > 0)
    neg_count = sum(1 for c in additive_attribs.contribs if c.value < 0)
    print(f"  Positive contributions: {pos_count}")
    print(f"  Negative contributions: {neg_count}")

    score_diff = additive_attribs.sum - low_risk_attribs.sum
    print(f"\nScore Difference: {score_diff:.3f}")
    print()


if __name__ == "__main__":
    main()
