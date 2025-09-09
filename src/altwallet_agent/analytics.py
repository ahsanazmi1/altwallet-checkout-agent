"""Analytics event schema and structured logging for AltWallet Checkout Agent.

This module provides a standardized analytics event schema to capture decision
outcomes and lifecycle telemetry. Events are logged as structured JSON for
easy ingestion into Redash, Metabase, or other analytics platforms.
"""

import json
import time
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, computed_field

from .logger import get_logger


class AnalyticsEventType(str, Enum):
    """Types of analytics events."""

    DECISION_OUTCOME = "decision_outcome"
    ROUTING_ANALYSIS = "routing_analysis"
    SCORING_UPDATE = "scoring_update"
    ERROR_OCCURRENCE = "error_occurrence"
    PERFORMANCE_METRIC = "performance_metric"
    BUSINESS_RULE_APPLIED = "business_rule_applied"


class DecisionOutcome(str, Enum):
    """Possible decision outcomes."""

    APPROVE = "APPROVE"
    REVIEW = "REVIEW"
    DECLINE = "DECLINE"
    ERROR = "ERROR"
    TIMEOUT = "TIMEOUT"


class ErrorSeverity(str, Enum):
    """Error severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class BusinessRuleType(str, Enum):
    """Types of business rules that can be applied."""

    KYC_REQUIRED = "kyc_required"
    LOYALTY_BOOST = "loyalty_boost"
    RISK_THRESHOLD = "risk_threshold"
    NETWORK_PREFERENCE = "network_preference"
    ACQUIRER_ROUTING = "acquirer_routing"
    FRAUD_CHECK = "fraud_check"
    COMPLIANCE_CHECK = "compliance_check"
    CUSTOM_RULE = "custom_rule"


class RoutingHint(BaseModel):
    """Routing hint information for analytics."""

    preferred_network: str = Field(..., description="Preferred payment network")
    preferred_acquirer: str | None = Field(None, description="Preferred acquirer")
    penalty_or_incentive: str = Field(..., description="Applied penalty or incentive")
    approval_odds: float | None = Field(None, description="Approval probability")
    confidence: float = Field(..., description="Confidence in routing recommendation")
    mcc_based_hint: str | None = Field(None, description="MCC-based routing hint")


class BusinessRule(BaseModel):
    """Business rule application details."""

    rule_type: BusinessRuleType = Field(..., description="Type of business rule")
    rule_id: str = Field(..., description="Unique rule identifier")
    rule_name: str = Field(..., description="Human-readable rule name")
    rule_version: str = Field(..., description="Rule version")
    applied: bool = Field(..., description="Whether rule was applied")
    impact_score: float = Field(
        ..., description="Impact on final decision (0.0 to 1.0)"
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Rule parameters"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class ErrorFlag(BaseModel):
    """Error flag information."""

    error_code: str = Field(..., description="Error code identifier")
    error_message: str = Field(..., description="Human-readable error message")
    severity: ErrorSeverity = Field(..., description="Error severity level")
    component: str = Field(..., description="Component where error occurred")
    stack_trace: str | None = Field(None, description="Stack trace if available")
    retryable: bool = Field(..., description="Whether error is retryable")
    timestamp: float = Field(..., description="When error occurred")


class PerformanceMetrics(BaseModel):
    """Performance and timing metrics."""

    total_latency_ms: float = Field(..., description="Total processing time")
    scoring_latency_ms: float = Field(..., description="Scoring calculation time")
    routing_latency_ms: float = Field(..., description="Routing calculation time")
    decision_latency_ms: float = Field(..., description="Decision logic time")
    external_api_calls: int = Field(..., description="Number of external API calls")
    external_api_latency_ms: float = Field(..., description="External API total time")
    memory_usage_mb: float | None = Field(None, description="Memory usage in MB")
    cpu_usage_percent: float | None = Field(None, description="CPU usage percentage")


class AnalyticsEvent(BaseModel):
    """Base analytics event schema."""

    # Core event identification
    event_id: str = Field(..., description="Unique event identifier")
    event_type: AnalyticsEventType = Field(..., description="Type of analytics event")
    timestamp: float = Field(..., description="Event timestamp (Unix epoch)")
    timestamp_iso: str = Field(..., description="ISO 8601 formatted timestamp")

    # Request context
    request_id: str = Field(..., description="Request identifier for correlation")
    session_id: str | None = Field(None, description="Session identifier")
    correlation_id: str | None = Field(None, description="Correlation ID for tracing")

    # Business context
    customer_id: str = Field(..., description="Customer identifier")
    merchant_id: str = Field(..., description="Merchant identifier")
    transaction_id: str | None = Field(None, description="Transaction identifier")

    # Decision outcomes
    decision: DecisionOutcome | None = Field(None, description="Final decision outcome")
    decision_reason: str | None = Field(
        None, description="Human-readable decision reason"
    )
    confidence_score: float | None = Field(
        None, description="Confidence in decision (0.0 to 1.0)"
    )

    # Business rules and actions
    business_rules: list[BusinessRule] = Field(
        default_factory=list, description="Applied business rules"
    )
    actions: list[str] = Field(
        default_factory=list, description="List of actions taken"
    )

    # Routing information
    routing_hint: RoutingHint | None = Field(
        None, description="Routing hint information"
    )

    # Performance metrics
    performance_metrics: PerformanceMetrics | None = Field(
        None, description="Performance and timing data"
    )

    # Error information
    error_flags: list[ErrorFlag] = Field(
        default_factory=list, description="Error flags and details"
    )
    has_errors: bool = Field(..., description="Whether any errors occurred")

    # Additional context
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional event metadata"
    )
    tags: list[str] = Field(
        default_factory=list, description="Event tags for categorization"
    )

    @computed_field
    def is_successful(self) -> bool:
        """Check if the event represents a successful operation."""
        return self.decision != DecisionOutcome.ERROR and not self.has_errors

    @computed_field
    def processing_time_category(self) -> str:
        """Categorize processing time for analysis."""
        if not self.performance_metrics:
            return "unknown"

        latency = self.performance_metrics.total_latency_ms
        if latency < 100:
            return "fast"
        elif latency < 500:
            return "normal"
        elif latency < 1000:
            return "slow"
        else:
            return "very_slow"

    @computed_field
    def risk_level(self) -> str:
        """Determine risk level based on decision and confidence."""
        if self.decision == DecisionOutcome.DECLINE:
            return "high"
        elif self.decision == DecisionOutcome.REVIEW:
            return "medium"
        elif self.decision == DecisionOutcome.APPROVE:
            if self.confidence_score and self.confidence_score < 0.7:
                return "medium"
            else:
                return "low"
        else:
            return "unknown"


class DecisionOutcomeEvent(AnalyticsEvent):
    """Analytics event for decision outcomes."""

    event_type: AnalyticsEventType = Field(default=AnalyticsEventType.DECISION_OUTCOME)

    # Decision-specific fields
    original_score: float | None = Field(None, description="Original risk score")
    final_score: float | None = Field(
        None, description="Final risk score after adjustments"
    )
    score_adjustments: list[dict[str, Any]] = Field(
        default_factory=list, description="Score adjustment details"
    )

    # Business impact
    transaction_amount: float | None = Field(None, description="Transaction amount")
    currency: str | None = Field(None, description="Transaction currency")
    revenue_impact: float | None = Field(None, description="Revenue impact of decision")

    # Risk assessment
    risk_factors: list[str] = Field(
        default_factory=list, description="Identified risk factors"
    )
    fraud_indicators: list[str] = Field(
        default_factory=list, description="Fraud indicators"
    )
    compliance_flags: list[str] = Field(
        default_factory=list, description="Compliance flags"
    )


class AnalyticsLogger:
    """Structured analytics logging for decision outcomes and telemetry."""

    def __init__(self) -> None:
        self.logger = get_logger(__name__)
        self.start_time = time.time()

    def _create_base_event(
        self,
        request_id: str,
        customer_id: str,
        merchant_id: str,
        event_type: AnalyticsEventType,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Create base event data."""
        now = time.time()
        return {
            "event_id": str(uuid4()),
            "event_type": event_type.value,
            "timestamp": now,
            "timestamp_iso": datetime.fromtimestamp(now, tz=UTC).isoformat(),
            "request_id": request_id,
            "customer_id": customer_id,
            "merchant_id": merchant_id,
            **kwargs,
        }

    def log_decision_outcome(
        self,
        request_id: str,
        customer_id: str,
        merchant_id: str,
        decision: DecisionOutcome,
        actions: list[str],
        routing_hint: RoutingHint | None = None,
        business_rules: list[BusinessRule] | None = None,
        error_flags: list[ErrorFlag] | None = None,
        performance_metrics: PerformanceMetrics | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> str:
        """Log a decision outcome event."""

        # Create event data
        event_data: dict[str, Any] = self._create_base_event(
            request_id=request_id,
            customer_id=customer_id,
            merchant_id=merchant_id,
            event_type=AnalyticsEventType.DECISION_OUTCOME,
            decision=decision.value,
            actions=actions,
            routing_hint=routing_hint.model_dump() if routing_hint else None,
            business_rules=(
                [rule.model_dump() for rule in business_rules] if business_rules else []
            ),
            error_flags=(
                [flag.model_dump() for flag in error_flags] if error_flags else []
            ),
            performance_metrics=(
                performance_metrics.model_dump() if performance_metrics else None
            ),
            has_errors=bool(error_flags),
            metadata=metadata or {},
            **kwargs,
        )

        # Log as structured JSON
        self.logger.info(
            "Decision outcome logged",
            event_id=event_data["event_id"],
            request_id=request_id,
            decision=decision.value,
            customer_id=customer_id,
            merchant_id=merchant_id,
        )

        # Log the full event data
        self.logger.info(
            "Analytics event",
            analytics_event=json.dumps(event_data, default=str),
        )

        return str(event_data["event_id"])

    def log_routing_analysis(
        self,
        request_id: str,
        customer_id: str,
        merchant_id: str,
        routing_hint: RoutingHint,
        performance_metrics: PerformanceMetrics | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Log a routing analysis event."""

        event_data: dict[str, Any] = self._create_base_event(
            request_id=request_id,
            customer_id=customer_id,
            merchant_id=merchant_id,
            event_type=AnalyticsEventType.ROUTING_ANALYSIS,
            routing_hint=routing_hint.model_dump(),
            performance_metrics=(
                performance_metrics.model_dump() if performance_metrics else None
            ),
            metadata=metadata or {},
        )

        self.logger.info(
            "Routing analysis logged",
            event_id=event_data["event_id"],
            request_id=request_id,
            preferred_network=routing_hint.preferred_network,
            confidence=routing_hint.confidence,
        )

        self.logger.info(
            "Analytics event",
            analytics_event=json.dumps(event_data, default=str),
        )

        return str(event_data["event_id"])

    def log_error_occurrence(
        self,
        request_id: str,
        customer_id: str,
        merchant_id: str,
        error_flag: ErrorFlag,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Log an error occurrence event."""

        event_data: dict[str, Any] = self._create_base_event(
            request_id=request_id,
            customer_id=customer_id,
            merchant_id=merchant_id,
            event_type=AnalyticsEventType.ERROR_OCCURRENCE,
            error_flags=[error_flag.model_dump()],
            has_errors=True,
            metadata=metadata or {},
        )

        self.logger.error(
            "Error occurrence logged",
            event_id=event_data["event_id"],
            request_id=request_id,
            error_code=error_flag.error_code,
            severity=error_flag.severity.value,
            component=error_flag.component,
        )

        self.logger.error(
            "Analytics event",
            analytics_event=json.dumps(event_data, default=str),
        )

        return str(event_data["event_id"])

    def log_performance_metric(
        self,
        request_id: str,
        customer_id: str,
        merchant_id: str,
        performance_metrics: PerformanceMetrics,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Log a performance metric event."""

        event_data: dict[str, Any] = self._create_base_event(
            request_id=request_id,
            customer_id=customer_id,
            merchant_id=merchant_id,
            event_type=AnalyticsEventType.PERFORMANCE_METRIC,
            performance_metrics=performance_metrics.model_dump(),
            metadata=metadata or {},
        )

        self.logger.info(
            "Performance metric logged",
            event_id=event_data["event_id"],
            request_id=request_id,
            total_latency_ms=performance_metrics.total_latency_ms,
            external_api_calls=performance_metrics.external_api_calls,
        )

        self.logger.info(
            "Analytics event",
            analytics_event=json.dumps(event_data, default=str),
        )

        return str(event_data["event_id"])


# Global analytics logger instance
_analytics_logger: AnalyticsLogger | None = None


def get_analytics_logger() -> AnalyticsLogger:
    """Get the global analytics logger instance."""
    global _analytics_logger

    if _analytics_logger is None:
        _analytics_logger = AnalyticsLogger()

    return _analytics_logger


def log_decision_outcome(
    request_id: str,
    customer_id: str,
    merchant_id: str,
    decision: DecisionOutcome,
    actions: list[str],
    routing_hint: RoutingHint | None = None,
    business_rules: list[BusinessRule] | None = None,
    error_flags: list[ErrorFlag] | None = None,
    performance_metrics: PerformanceMetrics | None = None,
    metadata: dict[str, Any] | None = None,
    **kwargs: Any,
) -> str:
    """Convenience function to log decision outcomes."""
    logger = get_analytics_logger()
    return logger.log_decision_outcome(
        request_id=request_id,
        customer_id=customer_id,
        merchant_id=merchant_id,
        decision=decision,
        actions=actions,
        routing_hint=routing_hint,
        business_rules=business_rules,
        error_flags=error_flags,
        performance_metrics=performance_metrics,
        metadata=metadata,
        **kwargs,
    )


def create_performance_metrics(
    total_latency_ms: float,
    scoring_latency_ms: float = 0.0,
    routing_latency_ms: float = 0.0,
    decision_latency_ms: float = 0.0,
    external_api_calls: int = 0,
    external_api_latency_ms: float = 0.0,
    memory_usage_mb: float | None = None,
    cpu_usage_percent: float | None = None,
) -> PerformanceMetrics:
    """Create performance metrics object."""
    return PerformanceMetrics(
        total_latency_ms=total_latency_ms,
        scoring_latency_ms=scoring_latency_ms,
        routing_latency_ms=routing_latency_ms,
        decision_latency_ms=decision_latency_ms,
        external_api_calls=external_api_calls,
        external_api_latency_ms=external_api_latency_ms,
        memory_usage_mb=memory_usage_mb,
        cpu_usage_percent=cpu_usage_percent,
    )


def create_business_rule(
    rule_type: BusinessRuleType,
    rule_id: str,
    rule_name: str,
    rule_version: str,
    applied: bool,
    impact_score: float,
    parameters: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> BusinessRule:
    """Create business rule object."""
    return BusinessRule(
        rule_type=rule_type,
        rule_id=rule_id,
        rule_name=rule_name,
        rule_version=rule_version,
        applied=applied,
        impact_score=impact_score,
        parameters=parameters or {},
        metadata=metadata or {},
    )


def create_error_flag(
    error_code: str,
    error_message: str,
    severity: ErrorSeverity,
    component: str,
    stack_trace: str | None = None,
    retryable: bool = False,
) -> ErrorFlag:
    """Create error flag object."""
    return ErrorFlag(
        error_code=error_code,
        error_message=error_message,
        severity=severity,
        component=component,
        stack_trace=stack_trace,
        retryable=retryable,
        timestamp=time.time(),
    )
