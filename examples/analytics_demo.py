#!/usr/bin/env python3
"""Demo script for the AltWallet Checkout Agent Analytics Module.

This script demonstrates how to use the analytics module to capture decision
outcomes and lifecycle telemetry with structured JSON logging compatible with
Redash/Metabase ingestion.
"""

import sys
import time
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import after path setup
from altwallet_agent.analytics import (
    AnalyticsLogger,
    BusinessRuleType,
    DecisionOutcome,
    DecisionOutcomeEvent,
    ErrorSeverity,
    RoutingHint,
    create_business_rule,
    create_error_flag,
    create_performance_metrics,
    log_decision_outcome,
)
from altwallet_agent.logger import configure_logging


def demonstrate_analytics():
    """Demonstrate the analytics module functionality."""

    print("📊 AltWallet Checkout Agent - Analytics Module Demo")
    print("=" * 60)

    # Configure logging
    configure_logging()

    # Get analytics logger
    analytics_logger = AnalyticsLogger()

    # Demo 1: Log a successful decision outcome
    print("\n📋 Demo 1: Successful Decision Outcome")
    print("-" * 50)

    # Create performance metrics
    perf_metrics = create_performance_metrics(
        total_latency_ms=245.7,
        scoring_latency_ms=120.3,
        routing_latency_ms=45.2,
        decision_latency_ms=80.2,
        external_api_calls=2,
        external_api_latency_ms=65.1,
    )

    # Create business rules
    business_rules = [
        create_business_rule(
            rule_type=BusinessRuleType.RISK_THRESHOLD,
            rule_id="risk_threshold_001",
            rule_name="Standard Risk Threshold",
            rule_version="1.0.0",
            applied=True,
            impact_score=0.8,
            parameters={"threshold": 75.0, "risk_level": "medium"},
        ),
        create_business_rule(
            rule_type=BusinessRuleType.LOYALTY_BOOST,
            rule_id="loyalty_boost_001",
            rule_name="Premium Customer Boost",
            rule_version="1.0.0",
            applied=True,
            impact_score=0.6,
            parameters={"customer_tier": "PREMIUM", "boost_amount": 10.0},
        ),
    ]

    # Log decision outcome
    event_id = analytics_logger.log_decision_outcome(
        request_id="req_analytics_001",
        customer_id="customer_123",
        merchant_id="merchant_456",
        decision=DecisionOutcome.APPROVE,
        actions=["risk_assessment", "loyalty_boost", "routing_optimization"],
        business_rules=business_rules,
        performance_metrics=perf_metrics,
        metadata={
            "transaction_amount": 150.00,
            "currency": "USD",
            "payment_method": "credit_card",
            "card_type": "visa",
        },
        confidence_score=0.85,
        decision_reason="Low risk transaction with premium customer boost",
    )

    print(f"✅ Decision outcome logged with event ID: {event_id}")

    # Demo 2: Log routing analysis
    print("\n📋 Demo 2: Routing Analysis")
    print("-" * 50)

    routing_hint = RoutingHint(
        preferred_network="visa",
        preferred_acquirer="acquirer_001",
        penalty_or_incentive="none",
        approval_odds=0.92,
        confidence=0.88,
        mcc_based_hint="retail_general",
    )

    routing_event_id = analytics_logger.log_routing_analysis(
        request_id="req_analytics_001",
        customer_id="customer_123",
        merchant_id="merchant_456",
        routing_hint=routing_hint,
        performance_metrics=perf_metrics,
        metadata={"mcc_code": "5311", "merchant_category": "Department Stores"},
    )

    print(f"✅ Routing analysis logged with event ID: {routing_event_id}")

    # Demo 3: Log error occurrence
    print("\n📋 Demo 3: Error Occurrence")
    print("-" * 50)

    error_flag = create_error_flag(
        error_code="EXTERNAL_API_TIMEOUT",
        error_message="External fraud check API timed out",
        severity=ErrorSeverity.MEDIUM,
        component="fraud_check_service",
        retryable=True,
    )

    error_event_id = analytics_logger.log_error_occurrence(
        request_id="req_analytics_001",
        customer_id="customer_123",
        merchant_id="merchant_456",
        error_flag=error_flag,
        metadata={"api_endpoint": "fraud-check.example.com", "timeout_ms": 5000},
    )

    print(f"✅ Error occurrence logged with event ID: {error_event_id}")

    # Demo 4: Log performance metrics
    print("\n📋 Demo 4: Performance Metrics")
    print("-" * 50)

    detailed_perf_metrics = create_performance_metrics(
        total_latency_ms=342.8,
        scoring_latency_ms=156.7,
        routing_latency_ms=52.1,
        decision_latency_ms=134.0,
        external_api_calls=3,
        external_api_latency_ms=89.2,
        memory_usage_mb=128.5,
        cpu_usage_percent=15.3,
    )

    perf_event_id = analytics_logger.log_performance_metric(
        request_id="req_analytics_001",
        customer_id="customer_123",
        merchant_id="merchant_456",
        performance_metrics=detailed_perf_metrics,
        metadata={"environment": "production", "instance_id": "prod-001"},
    )

    print(f"✅ Performance metrics logged with event ID: {perf_event_id}")

    # Demo 5: Use convenience function
    print("\n📋 Demo 5: Convenience Function")
    print("-" * 50)

    # Simulate a declined transaction
    declined_event_id = log_decision_outcome(
        request_id="req_analytics_002",
        customer_id="customer_789",
        merchant_id="merchant_456",
        decision=DecisionOutcome.DECLINE,
        actions=["risk_assessment", "fraud_check", "compliance_verification"],
        business_rules=[
            create_business_rule(
                rule_type=BusinessRuleType.FRAUD_CHECK,
                rule_id="fraud_check_001",
                rule_name="High Risk Transaction Check",
                rule_version="1.0.0",
                applied=True,
                impact_score=0.95,
                parameters={
                    "risk_score": 92.5,
                    "fraud_indicators": ["high_amount", "new_customer"],
                },
            )
        ],
        error_flags=[
            create_error_flag(
                error_code="HIGH_RISK_SCORE",
                error_message="Transaction risk score exceeds threshold",
                severity=ErrorSeverity.HIGH,
                component="risk_assessment_engine",
                retryable=False,
            )
        ],
        performance_metrics=create_performance_metrics(
            total_latency_ms=189.3, scoring_latency_ms=95.2, decision_latency_ms=94.1
        ),
        metadata={
            "transaction_amount": 2500.00,
            "currency": "USD",
            "risk_factors": ["high_amount", "new_customer", "unusual_location"],
        },
        confidence_score=0.92,
        decision_reason="High risk score due to transaction amount and customer profile",
    )

    print(f"✅ Declined decision logged with event ID: {declined_event_id}")

    # Demo 6: Show analytics event structure
    print("\n📋 Demo 6: Analytics Event Structure")
    print("-" * 50)

    # Create a sample event to show structure
    sample_event = DecisionOutcomeEvent(
        event_id="sample_event_001",
        event_type="decision_outcome",
        timestamp=time.time(),
        timestamp_iso="2025-01-15T10:30:00Z",
        request_id="req_sample_001",
        customer_id="customer_sample",
        merchant_id="merchant_sample",
        decision=DecisionOutcome.REVIEW,
        actions=["manual_review_required"],
        business_rules=[],
        error_flags=[],
        has_errors=False,
        metadata={},
        tags=["sample", "demo"],
        original_score=78.5,
        final_score=78.5,
        transaction_amount=500.00,
        currency="USD",
        risk_factors=["medium_risk_customer"],
    )

    print("Sample analytics event structure:")
    print(f"  Event ID: {sample_event.event_id}")
    print(f"  Event Type: {sample_event.event_type}")
    print(f"  Decision: {sample_event.decision}")
    print(f"  Risk Level: {sample_event.risk_level}")
    print(f"  Processing Time Category: {sample_event.processing_time_category}")
    print(f"  Is Successful: {sample_event.is_successful}")

    print("\n✅ Analytics module demo completed successfully!")
    print("\n📝 Key Features Demonstrated:")
    print("  • Structured JSON logging for Redash/Metabase ingestion")
    print("  • Decision outcome tracking with business rules")
    print("  • Routing analysis and performance metrics")
    print("  • Error occurrence logging with severity levels")
    print("  • Computed fields for risk analysis and categorization")
    print("  • Comprehensive metadata and tagging support")


def main():
    """Main function to run the demo."""
    try:
        demonstrate_analytics()
    except Exception as e:
        print(f"❌ Error running demo: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
