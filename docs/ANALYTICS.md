# Analytics Module

The Analytics Module provides a comprehensive event schema and structured logging system for capturing decision outcomes and lifecycle telemetry in the AltWallet Checkout Agent. All events are logged as structured JSON for easy ingestion into Redash, Metabase, or other analytics platforms.

## Overview

The analytics module captures critical business intelligence data including:

- **Decision Outcomes**: Transaction decisions with business rules and routing hints
- **Performance Metrics**: Latency, throughput, and resource utilization
- **Error Tracking**: Error occurrences with severity levels and retry information
- **Business Rules**: Applied business logic with impact scores and parameters
- **Routing Analysis**: Network preferences, acquirer routing, and confidence scores

## Event Schema

### Core Event Structure

All analytics events follow a standardized schema with these required fields:

```json
{
  "event_id": "uuid-12345",
  "event_type": "decision_outcome",
  "timestamp": 1640995200.0,
  "timestamp_iso": "2025-01-15T10:30:00Z",
  "request_id": "req_12345",
  "customer_id": "customer_123",
  "merchant_id": "merchant_456",
  "decision": "APPROVE",
  "actions": ["risk_assessment", "loyalty_boost"],
  "business_rules": [...],
  "routing_hint": {...},
  "performance_metrics": {...},
  "error_flags": [...],
  "has_errors": false,
  "metadata": {...},
  "tags": ["premium_customer", "low_risk"]
}
```

### Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `event_id` | string | Unique event identifier | `"uuid-12345"` |
| `request_id` | string | Request identifier for correlation | `"req_12345"` |
| `customer_id` | string | Customer identifier | `"customer_123"` |
| `merchant_id` | string | Merchant identifier | `"merchant_456"` |
| `timestamp` | float | Unix epoch timestamp | `1640995200.0` |
| `timestamp_iso` | string | ISO 8601 formatted timestamp | `"2025-01-15T10:30:00Z"` |

## Event Types

### 1. Decision Outcome Events

Capture the final decision and all contributing factors for each transaction.

**Key Fields:**
- `decision`: APPROVE, REVIEW, DECLINE, ERROR, TIMEOUT
- `actions`: List of actions taken during processing
- `business_rules`: Applied business rules with impact scores
- `routing_hint`: Network and acquirer preferences
- `confidence_score`: Confidence in the decision (0.0 to 1.0)
- `decision_reason`: Human-readable explanation

**Example:**
```json
{
  "event_type": "decision_outcome",
  "decision": "APPROVE",
  "actions": ["risk_assessment", "loyalty_boost", "routing_optimization"],
  "confidence_score": 0.85,
  "decision_reason": "Low risk transaction with premium customer boost",
  "original_score": 75.0,
  "final_score": 80.0,
  "transaction_amount": 150.00,
  "currency": "USD",
  "risk_factors": ["low_risk_customer", "familiar_location"],
  "fraud_indicators": [],
  "compliance_flags": []
}
```

### 2. Routing Analysis Events

Track routing decisions and network preferences for optimization.

**Key Fields:**
- `preferred_network`: Visa, Mastercard, etc.
- `preferred_acquirer`: Preferred acquirer identifier
- `penalty_or_incentive`: Surcharge, suppression, or none
- `approval_odds`: Probability of approval (0.0 to 1.0)
- `confidence`: Confidence in routing recommendation
- `mcc_based_hint`: MCC-based routing guidance

**Example:**
```json
{
  "event_type": "routing_analysis",
  "routing_hint": {
    "preferred_network": "visa",
    "preferred_acquirer": "acquirer_001",
    "penalty_or_incentive": "none",
    "approval_odds": 0.92,
    "confidence": 0.88,
    "mcc_based_hint": "retail_general"
  }
}
```

### 3. Performance Metric Events

Monitor system performance and identify bottlenecks.

**Key Fields:**
- `total_latency_ms`: Total processing time
- `scoring_latency_ms`: Risk scoring calculation time
- `routing_latency_ms`: Routing calculation time
- `decision_latency_ms`: Decision logic time
- `external_api_calls`: Number of external API calls
- `external_api_latency_ms`: External API total time
- `memory_usage_mb`: Memory usage in MB
- `cpu_usage_percent`: CPU usage percentage

**Example:**
```json
{
  "event_type": "performance_metric",
  "performance_metrics": {
    "total_latency_ms": 245.7,
    "scoring_latency_ms": 120.3,
    "routing_latency_ms": 45.2,
    "decision_latency_ms": 80.2,
    "external_api_calls": 2,
    "external_api_latency_ms": 65.1,
    "memory_usage_mb": 128.5,
    "cpu_usage_percent": 15.3
  }
}
```

### 4. Error Occurrence Events

Track errors with severity levels and retry information.

**Key Fields:**
- `error_code`: Unique error identifier
- `error_message`: Human-readable error description
- `severity`: LOW, MEDIUM, HIGH, CRITICAL
- `component`: Component where error occurred
- `stack_trace`: Stack trace if available
- `retryable`: Whether error is retryable
- `timestamp`: When error occurred

**Example:**
```json
{
  "event_type": "error_occurrence",
  "error_flags": [{
    "error_code": "EXTERNAL_API_TIMEOUT",
    "error_message": "External fraud check API timed out",
    "severity": "medium",
    "component": "fraud_check_service",
    "retryable": true,
    "timestamp": 1640995200.0
  }]
}
```

## Business Rules

Business rules capture the logic applied during decision making with impact scores.

**Structure:**
```json
{
  "rule_type": "risk_threshold",
  "rule_id": "risk_threshold_001",
  "rule_name": "Standard Risk Threshold",
  "rule_version": "1.0.0",
  "applied": true,
  "impact_score": 0.8,
  "parameters": {
    "threshold": 75.0,
    "risk_level": "medium"
  },
  "metadata": {
    "category": "risk_management",
    "priority": "high"
  }
}
```

**Rule Types:**
- `kyc_required`: Know Your Customer requirements
- `loyalty_boost`: Customer loyalty adjustments
- `risk_threshold`: Risk score thresholds
- `network_preference`: Payment network preferences
- `acquirer_routing`: Acquirer routing logic
- `fraud_check`: Fraud detection rules
- `compliance_check`: Regulatory compliance rules
- `custom_rule`: Custom business logic

## Computed Fields

The analytics module automatically computes several derived fields for analysis:

### Success Indicators
- `is_successful`: Boolean indicating successful operation
- `has_errors`: Boolean indicating error occurrence

### Performance Categories
- `processing_time_category`: fast (<100ms), normal (<500ms), slow (<1000ms), very_slow (≥1000ms)

### Risk Assessment
- `risk_level`: low, medium, high, unknown based on decision and confidence

## Redash/Metabase Integration

### Data Ingestion

The structured JSON logs are designed for easy ingestion into analytics platforms:

1. **Log Parsing**: Parse JSON logs using standard log aggregation tools
2. **Field Extraction**: Extract specific fields for analysis
3. **Time Series**: Use timestamp fields for time-based analysis
4. **Categorization**: Use tags and computed fields for grouping

### Sample Queries

**Decision Success Rate by Merchant:**
```sql
SELECT 
  merchant_id,
  COUNT(*) as total_decisions,
  SUM(CASE WHEN decision = 'APPROVE' THEN 1 ELSE 0 END) as approvals,
  AVG(CASE WHEN decision = 'APPROVE' THEN 1.0 ELSE 0.0 END) as approval_rate
FROM analytics_events 
WHERE event_type = 'decision_outcome'
GROUP BY merchant_id
ORDER BY approval_rate DESC;
```

**Performance Analysis by Time:**
```sql
SELECT 
  DATE_TRUNC('hour', FROM_UNIXTIME(timestamp)) as hour,
  AVG(performance_metrics.total_latency_ms) as avg_latency,
  COUNT(*) as request_count
FROM analytics_events 
WHERE event_type = 'decision_outcome'
  AND performance_metrics IS NOT NULL
GROUP BY hour
ORDER BY hour;
```

**Error Rate by Component:**
```sql
SELECT 
  error_flags.component,
  COUNT(*) as error_count,
  AVG(CASE WHEN error_flags.retryable THEN 1.0 ELSE 0.0 END) as retryable_rate
FROM analytics_events 
WHERE event_type = 'error_occurrence'
GROUP BY error_flags.component
ORDER BY error_count DESC;
```

**Business Rule Impact Analysis:**
```sql
SELECT 
  business_rules.rule_type,
  business_rules.rule_name,
  COUNT(*) as application_count,
  AVG(business_rules.impact_score) as avg_impact,
  AVG(CASE WHEN decision = 'APPROVE' THEN 1.0 ELSE 0.0 END) as approval_rate
FROM analytics_events 
WHERE event_type = 'decision_outcome'
  AND business_rules IS NOT NULL
GROUP BY business_rules.rule_type, business_rules.rule_name
ORDER BY application_count DESC;
```

## Usage Examples

### Basic Decision Logging

```python
from altwallet_agent.analytics import log_decision_outcome, DecisionOutcome

# Log a simple decision
event_id = log_decision_outcome(
    request_id="req_12345",
    customer_id="customer_123",
    merchant_id="merchant_456",
    decision=DecisionOutcome.APPROVE,
    actions=["risk_assessment", "fraud_check"]
)
```

### Advanced Decision Logging with Business Rules

```python
from altwallet_agent.analytics import (
    log_decision_outcome, DecisionOutcome, create_business_rule,
    BusinessRuleType, create_performance_metrics
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
        parameters={"threshold": 75.0}
    )
]

# Create performance metrics
perf_metrics = create_performance_metrics(
    total_latency_ms=245.7,
    scoring_latency_ms=120.3,
    routing_latency_ms=45.2,
    decision_latency_ms=80.2
)

# Log decision with full context
event_id = log_decision_outcome(
    request_id="req_12345",
    customer_id="customer_123",
    merchant_id="merchant_456",
    decision=DecisionOutcome.APPROVE,
    actions=["risk_assessment", "fraud_check"],
    business_rules=business_rules,
    performance_metrics=perf_metrics,
    confidence_score=0.85,
    decision_reason="Low risk transaction"
)
```

### Error Logging

```python
from altwallet_agent.analytics import (
    get_analytics_logger, create_error_flag, ErrorSeverity
)

logger = get_analytics_logger()

# Create error flag
error_flag = create_error_flag(
    error_code="EXTERNAL_API_TIMEOUT",
    error_message="External fraud check API timed out",
    severity=ErrorSeverity.MEDIUM,
    component="fraud_check_service",
    retryable=True
)

# Log error occurrence
event_id = logger.log_error_occurrence(
    request_id="req_12345",
    customer_id="customer_123",
    merchant_id="merchant_456",
    error_flag=error_flag,
    metadata={"api_endpoint": "fraud-check.example.com"}
)
```

### Performance Monitoring

```python
from altwallet_agent.analytics import (
    get_analytics_logger, create_performance_metrics
)

logger = get_analytics_logger()

# Create performance metrics
perf_metrics = create_performance_metrics(
    total_latency_ms=342.8,
    scoring_latency_ms=156.7,
    routing_latency_ms=52.1,
    decision_latency_ms=134.0,
    external_api_calls=3,
    external_api_latency_ms=89.2,
    memory_usage_mb=128.5,
    cpu_usage_percent=15.3
)

# Log performance metrics
event_id = logger.log_performance_metric(
    request_id="req_12345",
    customer_id="customer_123",
    merchant_id="merchant_456",
    performance_metrics=perf_metrics,
    metadata={"environment": "production"}
)
```

## Configuration

### Logging Setup

The analytics module integrates with the existing structured logging system:

```python
from altwallet_agent.logger import configure_logging
from altwallet_agent.analytics import get_analytics_logger

# Configure logging
configure_logging()

# Get analytics logger
analytics_logger = get_analytics_logger()
```

### Environment Variables

Configure analytics behavior through environment variables:

```bash
# Enable/disable analytics logging
ANALYTICS_ENABLED=true

# Log level for analytics events
ANALYTICS_LOG_LEVEL=INFO

# Maximum metadata size (bytes)
ANALYTICS_MAX_METADATA_SIZE=8192

# Enable performance metrics collection
ANALYTICS_COLLECT_PERFORMANCE=true
```

## Best Practices

### 1. Consistent Request IDs
- Use the same `request_id` across all events for a single transaction
- Generate unique request IDs for each transaction
- Include request IDs in error logs for correlation

### 2. Meaningful Metadata
- Keep metadata concise and relevant
- Use consistent key names across events
- Avoid sensitive information in metadata

### 3. Performance Monitoring
- Log performance metrics for all critical operations
- Set appropriate thresholds for alerting
- Monitor trends over time

### 4. Error Tracking
- Use descriptive error codes and messages
- Set appropriate severity levels
- Include retry information for operational decisions

### 5. Business Rule Documentation
- Use descriptive rule names and versions
- Document rule parameters and impact scores
- Track rule changes over time

## Monitoring and Alerting

### Key Metrics to Monitor

1. **Decision Success Rate**: Percentage of successful decisions
2. **Average Latency**: Processing time trends
3. **Error Rate**: Error frequency by component
4. **Business Rule Impact**: Rule application effectiveness
5. **Routing Efficiency**: Network and acquirer performance

### Alerting Thresholds

- **High Error Rate**: >5% error rate in any component
- **Performance Degradation**: >2x increase in average latency
- **Decision Failures**: >10% decline in success rate
- **Critical Errors**: Any CRITICAL severity errors

## Troubleshooting

### Common Issues

1. **Missing Events**: Check logging configuration and permissions
2. **Incomplete Data**: Verify all required fields are provided
3. **Performance Impact**: Monitor logging overhead in high-volume scenarios
4. **Data Quality**: Validate event schema compliance

### Debug Commands

```python
# Check analytics logger status
logger = get_analytics_logger()
print(f"Logger active: {logger is not None}")

# Verify event creation
event = DecisionOutcomeEvent(...)
print(f"Event valid: {event.model_validate(event.model_dump())}")
```

## Future Enhancements

- **Real-time Streaming**: Kafka/RabbitMQ integration for real-time analytics
- **Machine Learning**: Automated anomaly detection and pattern recognition
- **Advanced Metrics**: A/B testing support and statistical analysis
- **Custom Dashboards**: Built-in visualization and reporting tools
- **Data Retention**: Configurable data retention and archival policies
