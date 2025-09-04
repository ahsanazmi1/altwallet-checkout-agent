"""Tests for the analytics module."""

import pytest
import time
from unittest.mock import patch

from src.altwallet_agent.analytics import (
    AnalyticsEventType,
    DecisionOutcome,
    ErrorSeverity,
    BusinessRuleType,
    RoutingHint,
    BusinessRule,
    ErrorFlag,
    PerformanceMetrics,
    AnalyticsEvent,
    DecisionOutcomeEvent,
    AnalyticsLogger,
    get_analytics_logger,
    log_decision_outcome,
    create_performance_metrics,
    create_business_rule,
    create_error_flag
)


class TestAnalyticsEnums:
    """Test analytics enum values."""
    
    def test_analytics_event_types(self):
        """Test analytics event type enum values."""
        assert AnalyticsEventType.DECISION_OUTCOME == "decision_outcome"
        assert AnalyticsEventType.ROUTING_ANALYSIS == "routing_analysis"
        assert AnalyticsEventType.SCORING_UPDATE == "scoring_update"
        assert AnalyticsEventType.ERROR_OCCURRENCE == "error_occurrence"
        assert AnalyticsEventType.PERFORMANCE_METRIC == "performance_metric"
        assert AnalyticsEventType.BUSINESS_RULE_APPLIED == "business_rule_applied"
    
    def test_decision_outcomes(self):
        """Test decision outcome enum values."""
        assert DecisionOutcome.APPROVE == "APPROVE"
        assert DecisionOutcome.REVIEW == "REVIEW"
        assert DecisionOutcome.DECLINE == "DECLINE"
        assert DecisionOutcome.ERROR == "ERROR"
        assert DecisionOutcome.TIMEOUT == "TIMEOUT"
    
    def test_error_severities(self):
        """Test error severity enum values."""
        assert ErrorSeverity.LOW == "low"
        assert ErrorSeverity.MEDIUM == "medium"
        assert ErrorSeverity.HIGH == "high"
        assert ErrorSeverity.CRITICAL == "critical"
    
    def test_business_rule_types(self):
        """Test business rule type enum values."""
        assert BusinessRuleType.KYC_REQUIRED == "kyc_required"
        assert BusinessRuleType.LOYALTY_BOOST == "loyalty_boost"
        assert BusinessRuleType.RISK_THRESHOLD == "risk_threshold"
        assert BusinessRuleType.NETWORK_PREFERENCE == "network_preference"
        assert BusinessRuleType.ACQUIRER_ROUTING == "acquirer_routing"
        assert BusinessRuleType.FRAUD_CHECK == "fraud_check"
        assert BusinessRuleType.COMPLIANCE_CHECK == "compliance_check"
        assert BusinessRuleType.CUSTOM_RULE == "custom_rule"


class TestRoutingHint:
    """Test routing hint model."""
    
    def test_routing_hint_creation(self):
        """Test routing hint creation."""
        hint = RoutingHint(
            preferred_network="visa",
            preferred_acquirer="acquirer_001",
            penalty_or_incentive="none",
            approval_odds=0.85,
            confidence=0.9,
            mcc_based_hint="retail_general"
        )
        
        assert hint.preferred_network == "visa"
        assert hint.preferred_acquirer == "acquirer_001"
        assert hint.penalty_or_incentive == "none"
        assert hint.approval_odds == 0.85
        assert hint.confidence == 0.9
        assert hint.mcc_based_hint == "retail_general"
    
    def test_routing_hint_optional_fields(self):
        """Test routing hint with optional fields."""
        hint = RoutingHint(
            preferred_network="mastercard",
            penalty_or_incentive="surcharge",
            confidence=0.75
        )
        
        assert hint.preferred_network == "mastercard"
        assert hint.preferred_acquirer is None
        assert hint.approval_odds is None
        assert hint.mcc_based_hint is None
        assert hint.penalty_or_incentive == "surcharge"
        assert hint.confidence == 0.75


class TestBusinessRule:
    """Test business rule model."""
    
    def test_business_rule_creation(self):
        """Test business rule creation."""
        rule = BusinessRule(
            rule_type=BusinessRuleType.RISK_THRESHOLD,
            rule_id="risk_001",
            rule_name="Standard Risk Threshold",
            rule_version="1.0.0",
            applied=True,
            impact_score=0.8,
            parameters={"threshold": 75.0},
            metadata={"category": "risk_management"}
        )
        
        assert rule.rule_type == BusinessRuleType.RISK_THRESHOLD
        assert rule.rule_id == "risk_001"
        assert rule.rule_name == "Standard Risk Threshold"
        assert rule.rule_version == "1.0.0"
        assert rule.applied is True
        assert rule.impact_score == 0.8
        assert rule.parameters == {"threshold": 75.0}
        assert rule.metadata == {"category": "risk_management"}


class TestErrorFlag:
    """Test error flag model."""
    
    def test_error_flag_creation(self):
        """Test error flag creation."""
        flag = ErrorFlag(
            error_code="API_TIMEOUT",
            error_message="External API timed out",
            severity=ErrorSeverity.MEDIUM,
            component="fraud_check_service",
            stack_trace="Traceback...",
            retryable=True,
            timestamp=time.time()
        )
        
        assert flag.error_code == "API_TIMEOUT"
        assert flag.error_message == "External API timed out"
        assert flag.severity == ErrorSeverity.MEDIUM
        assert flag.component == "fraud_check_service"
        assert flag.stack_trace == "Traceback..."
        assert flag.retryable is True
        assert flag.timestamp > 0


class TestPerformanceMetrics:
    """Test performance metrics model."""
    
    def test_performance_metrics_creation(self):
        """Test performance metrics creation."""
        metrics = PerformanceMetrics(
            total_latency_ms=250.0,
            scoring_latency_ms=120.0,
            routing_latency_ms=50.0,
            decision_latency_ms=80.0,
            external_api_calls=2,
            external_api_latency_ms=60.0,
            memory_usage_mb=128.0,
            cpu_usage_percent=15.0
        )
        
        assert metrics.total_latency_ms == 250.0
        assert metrics.scoring_latency_ms == 120.0
        assert metrics.routing_latency_ms == 50.0
        assert metrics.decision_latency_ms == 80.0
        assert metrics.external_api_calls == 2
        assert metrics.external_api_latency_ms == 60.0
        assert metrics.memory_usage_mb == 128.0
        assert metrics.cpu_usage_percent == 15.0
    
    def test_performance_metrics_optional_fields(self):
        """Test performance metrics with optional fields."""
        metrics = PerformanceMetrics(
            total_latency_ms=150.0,
            scoring_latency_ms=75.0,
            routing_latency_ms=25.0,
            decision_latency_ms=50.0,
            external_api_calls=1,
            external_api_latency_ms=30.0
        )
        
        assert metrics.total_latency_ms == 150.0
        assert metrics.memory_usage_mb is None
        assert metrics.cpu_usage_percent is None


class TestAnalyticsEvent:
    """Test base analytics event model."""
    
    def test_analytics_event_creation(self):
        """Test analytics event creation."""
        event = AnalyticsEvent(
            event_id="event_001",
            event_type=AnalyticsEventType.DECISION_OUTCOME,
            timestamp=time.time(),
            timestamp_iso="2025-01-15T10:30:00Z",
            request_id="req_001",
            customer_id="customer_123",
            merchant_id="merchant_456",
            decision=DecisionOutcome.APPROVE,
            actions=["risk_assessment"],
            business_rules=[],
            error_flags=[],
            has_errors=False,
            metadata={},
            tags=["test"]
        )
        
        assert event.event_id == "event_001"
        assert event.event_type == AnalyticsEventType.DECISION_OUTCOME
        assert event.request_id == "req_001"
        assert event.customer_id == "customer_123"
        assert event.merchant_id == "merchant_456"
        assert event.decision == DecisionOutcome.APPROVE
        assert event.actions == ["risk_assessment"]
        assert event.has_errors is False
        assert event.tags == ["test"]
    
    def test_analytics_event_computed_fields(self):
        """Test analytics event computed fields."""
        event = AnalyticsEvent(
            event_id="event_001",
            event_type=AnalyticsEventType.DECISION_OUTCOME,
            timestamp=time.time(),
            timestamp_iso="2025-01-15T10:30:00Z",
            request_id="req_001",
            customer_id="customer_123",
            merchant_id="merchant_456",
            decision=DecisionOutcome.APPROVE,
            actions=[],
            business_rules=[],
            error_flags=[],
            has_errors=False,
            metadata={},
            tags=[]
        )
        
        assert event.is_successful is True
        assert event.processing_time_category == "unknown"
        assert event.risk_level == "low"
    
    def test_analytics_event_with_performance_metrics(self):
        """Test analytics event with performance metrics."""
        metrics = PerformanceMetrics(
            total_latency_ms=300.0,
            scoring_latency_ms=150.0,
            routing_latency_ms=75.0,
            decision_latency_ms=75.0,
            external_api_calls=2,
            external_api_latency_ms=80.0
        )
        
        event = AnalyticsEvent(
            event_id="event_001",
            event_type=AnalyticsEventType.DECISION_OUTCOME,
            timestamp=time.time(),
            timestamp_iso="2025-01-15T10:30:00Z",
            request_id="req_001",
            customer_id="customer_123",
            merchant_id="merchant_456",
            decision=DecisionOutcome.APPROVE,
            actions=[],
            business_rules=[],
            error_flags=[],
            has_errors=False,
            performance_metrics=metrics,
            metadata={},
            tags=[]
        )
        
        assert event.processing_time_category == "normal"
    
    def test_analytics_event_risk_levels(self):
        """Test analytics event risk level computation."""
        # Test decline decision
        decline_event = AnalyticsEvent(
            event_id="event_001",
            event_type=AnalyticsEventType.DECISION_OUTCOME,
            timestamp=time.time(),
            timestamp_iso="2025-01-15T10:30:00Z",
            request_id="req_001",
            customer_id="customer_123",
            merchant_id="merchant_456",
            decision=DecisionOutcome.DECLINE,
            actions=[],
            business_rules=[],
            error_flags=[],
            has_errors=False,
            metadata={},
            tags=[]
        )
        assert decline_event.risk_level == "high"
        
        # Test review decision
        review_event = AnalyticsEvent(
            event_id="event_002",
            event_type=AnalyticsEventType.DECISION_OUTCOME,
            timestamp=time.time(),
            timestamp_iso="2025-01-15T10:30:00Z",
            request_id="req_002",
            customer_id="customer_123",
            merchant_id="merchant_456",
            decision=DecisionOutcome.REVIEW,
            actions=[],
            business_rules=[],
            error_flags=[],
            has_errors=False,
            metadata={},
            tags=[]
        )
        assert review_event.risk_level == "medium"
        
        # Test approve decision with low confidence
        low_confidence_event = AnalyticsEvent(
            event_id="event_003",
            event_type=AnalyticsEventType.DECISION_OUTCOME,
            timestamp=time.time(),
            timestamp_iso="2025-01-15T10:30:00Z",
            request_id="req_003",
            customer_id="customer_123",
            merchant_id="merchant_456",
            decision=DecisionOutcome.APPROVE,
            actions=[],
            business_rules=[],
            error_flags=[],
            has_errors=False,
            confidence_score=0.6,
            metadata={},
            tags=[]
        )
        assert low_confidence_event.risk_level == "medium"


class TestDecisionOutcomeEvent:
    """Test decision outcome event model."""
    
    def test_decision_outcome_event_creation(self):
        """Test decision outcome event creation."""
        event = DecisionOutcomeEvent(
            event_id="event_001",
            event_type=AnalyticsEventType.DECISION_OUTCOME,
            timestamp=time.time(),
            timestamp_iso="2025-01-15T10:30:00Z",
            request_id="req_001",
            customer_id="customer_123",
            merchant_id="merchant_456",
            decision=DecisionOutcome.APPROVE,
            actions=["risk_assessment"],
            business_rules=[],
            error_flags=[],
            has_errors=False,
            metadata={},
            tags=[],
            original_score=75.0,
            final_score=80.0,
            transaction_amount=100.0,
            currency="USD",
            risk_factors=["low_risk_customer"]
        )
        
        assert event.original_score == 75.0
        assert event.final_score == 80.0
        assert event.transaction_amount == 100.0
        assert event.currency == "USD"
        assert event.risk_factors == ["low_risk_customer"]


class TestAnalyticsLogger:
    """Test analytics logger."""
    
    def test_analytics_logger_creation(self):
        """Test analytics logger creation."""
        logger = AnalyticsLogger()
        assert logger is not None
        assert logger.start_time > 0
    
    @patch('src.altwallet_agent.analytics.get_logger')
    def test_log_decision_outcome(self, mock_get_logger):
        """Test logging decision outcome."""
        mock_logger = mock_get_logger.return_value
        
        logger = AnalyticsLogger()
        event_id = logger.log_decision_outcome(
            request_id="req_001",
            customer_id="customer_123",
            merchant_id="merchant_456",
            decision=DecisionOutcome.APPROVE,
            actions=["risk_assessment"]
        )
        
        assert event_id is not None
        assert len(event_id) > 0
        
        # Verify logger was called
        assert mock_logger.info.call_count >= 2
    
    @patch('src.altwallet_agent.analytics.get_logger')
    def test_log_routing_analysis(self, mock_get_logger):
        """Test logging routing analysis."""
        mock_logger = mock_get_logger.return_value
        
        logger = AnalyticsLogger()
        routing_hint = RoutingHint(
            preferred_network="visa",
            penalty_or_incentive="none",
            confidence=0.9
        )
        
        event_id = logger.log_routing_analysis(
            request_id="req_001",
            customer_id="customer_123",
            merchant_id="merchant_456",
            routing_hint=routing_hint
        )
        
        assert event_id is not None
        assert len(event_id) > 0
        
        # Verify logger was called
        assert mock_logger.info.call_count >= 2
    
    @patch('src.altwallet_agent.analytics.get_logger')
    def test_log_error_occurrence(self, mock_get_logger):
        """Test logging error occurrence."""
        mock_logger = mock_get_logger.return_value
        
        logger = AnalyticsLogger()
        error_flag = create_error_flag(
            error_code="TEST_ERROR",
            error_message="Test error message",
            severity=ErrorSeverity.LOW,
            component="test_component"
        )
        
        event_id = logger.log_error_occurrence(
            request_id="req_001",
            customer_id="customer_123",
            merchant_id="merchant_456",
            error_flag=error_flag
        )
        
        assert event_id is not None
        assert len(event_id) > 0
        
        # Verify logger was called
        assert mock_logger.error.call_count >= 2


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_create_performance_metrics(self):
        """Test create_performance_metrics function."""
        metrics = create_performance_metrics(
            total_latency_ms=200.0,
            scoring_latency_ms=100.0,
            routing_latency_ms=50.0,
            decision_latency_ms=50.0,
            external_api_calls=1,
            external_api_latency_ms=40.0
        )
        
        assert isinstance(metrics, PerformanceMetrics)
        assert metrics.total_latency_ms == 200.0
        assert metrics.scoring_latency_ms == 100.0
        assert metrics.routing_latency_ms == 50.0
        assert metrics.decision_latency_ms == 50.0
        assert metrics.external_api_calls == 1
        assert metrics.external_api_latency_ms == 40.0
    
    def test_create_business_rule(self):
        """Test create_business_rule function."""
        rule = create_business_rule(
            rule_type=BusinessRuleType.LOYALTY_BOOST,
            rule_id="loyalty_001",
            rule_name="Premium Customer Boost",
            rule_version="1.0.0",
            applied=True,
            impact_score=0.7
        )
        
        assert isinstance(rule, BusinessRule)
        assert rule.rule_type == BusinessRuleType.LOYALTY_BOOST
        assert rule.rule_id == "loyalty_001"
        assert rule.rule_name == "Premium Customer Boost"
        assert rule.rule_version == "1.0.0"
        assert rule.applied is True
        assert rule.impact_score == 0.7
    
    def test_create_error_flag(self):
        """Test create_error_flag function."""
        flag = create_error_flag(
            error_code="TEST_ERROR",
            error_message="Test error",
            severity=ErrorSeverity.MEDIUM,
            component="test_component"
        )
        
        assert isinstance(flag, ErrorFlag)
        assert flag.error_code == "TEST_ERROR"
        assert flag.error_message == "Test error"
        assert flag.severity == ErrorSeverity.MEDIUM
        assert flag.component == "test_component"
        assert flag.timestamp > 0


class TestGlobalFunctions:
    """Test global functions."""
    
    def test_get_analytics_logger(self):
        """Test get_analytics_logger function."""
        logger = get_analytics_logger()
        assert isinstance(logger, AnalyticsLogger)
        
        # Should return the same instance
        logger2 = get_analytics_logger()
        assert logger is logger2
    
    @patch('src.altwallet_agent.analytics.get_analytics_logger')
    def test_log_decision_outcome_global(self, mock_get_logger):
        """Test global log_decision_outcome function."""
        mock_logger = mock_get_logger.return_value
        mock_logger.log_decision_outcome.return_value = "event_123"
        
        event_id = log_decision_outcome(
            request_id="req_001",
            customer_id="customer_123",
            merchant_id="merchant_456",
            decision=DecisionOutcome.APPROVE,
            actions=["risk_assessment"]
        )
        
        assert event_id == "event_123"
        mock_logger.log_decision_outcome.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
