# Analytics Dashboard Setup

This directory contains starter SQL queries and dashboard configurations for Redash and Metabase to visualize key AltWallet Checkout Agent metrics.

## Overview

The analytics configurations provide ready-to-use dashboards for monitoring:

- **Approval Rate**: Transaction approval success rates by merchant, time, and customer segment
- **Decline Reasons**: Distribution of decline reasons and fraud indicators
- **Decision Latency**: Performance metrics and processing time analysis
- **Surcharge vs Suppression**: Routing optimization and fee structure analysis
- **Loyalty Events**: Customer loyalty program effectiveness and engagement

## Directory Structure

```
analytics/
├── README.md                           # This file
├── sql/                               # SQL queries for each metric
│   ├── approval_rate.sql
│   ├── decline_reasons.sql
│   ├── decision_latency.sql
│   ├── surcharge_suppression.sql
│   └── loyalty_events.sql
├── redash/                            # Redash dashboard configurations
│   ├── dashboard_config.json
│   ├── queries/
│   │   ├── approval_rate.json
│   │   ├── decline_reasons.json
│   │   ├── decision_latency.json
│   │   ├── surcharge_suppression.json
│   │   └── loyalty_events.json
│   └── setup_instructions.md
└── metabase/                          # Metabase dashboard configurations
    ├── dashboard_config.json
    ├── questions/
    │   ├── approval_rate.json
    │   ├── decline_reasons.json
    │   ├── decision_latency.json
    │   ├── surcharge_suppression.json
    │   └── loyalty_events.json
    └── setup_instructions.md
```

## Prerequisites

### 1. Data Source Setup

Ensure your analytics platform can access the structured JSON logs from the AltWallet Checkout Agent. The logs contain these key fields:

- `event_type`: Type of analytics event
- `decision`: Transaction decision (APPROVE, REVIEW, DECLINE, ERROR, TIMEOUT)
- `timestamp`: Event timestamp for time-based analysis
- `merchant_id`: Merchant identifier for segmentation
- `customer_id`: Customer identifier for analysis
- `performance_metrics`: Latency and performance data
- `routing_hint`: Network preferences and fee structures
- `business_rules`: Applied business logic and actions

### 2. Log Ingestion

The analytics events are logged as structured JSON. You'll need to:

1. **Parse JSON logs** using your log aggregation tool (ELK, Splunk, etc.)
2. **Extract fields** into a database or data warehouse
3. **Create tables/collections** for the analytics data

### 3. Data Schema

The analytics events follow this structure:

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

## Setup Instructions

### Redash Setup

1. **Import Dashboard Configuration**
   ```bash
   # Copy the dashboard configuration
   cp analytics/redash/dashboard_config.json /path/to/redash/imports/
   ```

2. **Import Individual Queries**
   ```bash
   # Import each query configuration
   cp analytics/redash/queries/*.json /path/to/redash/imports/
   ```

3. **Configure Data Source**
   - Connect to your analytics database
   - Update query parameters if needed
   - Test queries for data access

4. **Customize Dashboard**
   - Adjust time ranges and filters
   - Modify chart types and colors
   - Add additional metrics as needed

### Metabase Setup

1. **Import Dashboard Configuration**
   ```bash
   # Copy the dashboard configuration
   cp analytics/metabase/dashboard_config.json /path/to/metabase/imports/
   ```

2. **Import Individual Questions**
   ```bash
   # Import each question configuration
   cp analytics/metabase/questions/*.json /path/to/metabase/imports/
   ```

3. **Configure Database Connection**
   - Connect to your analytics database
   - Verify table/collection access
   - Test query execution

4. **Customize Dashboard**
   - Adjust visualization types
   - Modify filters and parameters
   - Add custom metrics and alerts

## Key Metrics Explained

### 1. Approval Rate

**What it measures**: Percentage of transactions that are approved vs declined/reviewed

**Business value**: 
- Monitor risk assessment effectiveness
- Identify trends in approval patterns
- Optimize business rules and thresholds

**Key dimensions**:
- Time (hourly, daily, weekly trends)
- Merchant (performance by business)
- Customer segment (risk profiles)
- Transaction amount (risk by size)

### 2. Decline Reasons Distribution

**What it measures**: Breakdown of why transactions are declined

**Business value**:
- Identify fraud patterns
- Optimize risk rules
- Reduce false positives
- Improve customer experience

**Key categories**:
- High risk score
- Fraud indicators
- Compliance flags
- Business rule violations

### 3. Decision Latency

**What it measures**: Processing time for transaction decisions

**Business value**:
- Monitor system performance
- Identify bottlenecks
- Optimize processing efficiency
- Ensure SLA compliance

**Key metrics**:
- Total processing time
- Scoring calculation time
- Routing decision time
- External API response time

### 4. Surcharge vs Suppression

**What it measures**: Frequency of fee adjustments in routing decisions

**Business value**:
- Optimize network routing
- Balance cost vs approval rates
- Monitor fee structure effectiveness
- Identify routing optimization opportunities

**Key insights**:
- Network preference patterns
- Fee impact on decisions
- Acquirer performance
- MCC-based routing effectiveness

### 5. Loyalty Events

**What it measures**: Customer loyalty program engagement and effectiveness

**Business value**:
- Monitor loyalty program usage
- Identify high-value customers
- Optimize loyalty incentives
- Measure program ROI

**Key metrics**:
- Points earned/redeemed
- Customer tier distribution
- Loyalty boost effectiveness
- Program engagement rates

## Customization

### Adding New Metrics

1. **Create SQL Query**: Add new query file in `sql/` directory
2. **Update Dashboard**: Add visualization to dashboard configuration
3. **Test and Validate**: Ensure data accuracy and performance

### Modifying Existing Metrics

1. **Update SQL**: Modify query logic and parameters
2. **Adjust Visualization**: Change chart types, colors, and filters
3. **Test Changes**: Validate modifications in test environment

### Performance Optimization

1. **Indexing**: Ensure proper database indexing on key fields
2. **Query Optimization**: Use efficient SQL patterns and joins
3. **Caching**: Implement appropriate caching strategies
4. **Data Retention**: Configure appropriate data retention policies

## Troubleshooting

### Common Issues

1. **Data Not Loading**
   - Check database connection
   - Verify table/collection access
   - Check query syntax and permissions

2. **Performance Issues**
   - Review query execution plans
   - Check database indexing
   - Optimize complex joins and aggregations

3. **Visualization Problems**
   - Verify data types and formats
   - Check for null/empty values
   - Adjust chart configuration

### Debug Commands

```sql
-- Check data availability
SELECT COUNT(*) FROM analytics_events WHERE event_type = 'decision_outcome';

-- Verify recent data
SELECT MAX(timestamp), MIN(timestamp) FROM analytics_events;

-- Check data quality
SELECT decision, COUNT(*) FROM analytics_events 
WHERE event_type = 'decision_outcome' 
GROUP BY decision;
```

## Support

For issues or questions:

1. **Check logs**: Review application and database logs
2. **Verify data**: Ensure analytics events are being generated
3. **Test queries**: Run SQL queries directly against database
4. **Review configuration**: Check dashboard and query settings

## Future Enhancements

- **Real-time dashboards**: Live monitoring and alerting
- **Advanced analytics**: Machine learning insights and predictions
- **Custom metrics**: Business-specific KPIs and calculations
- **Integration**: Connect with other business intelligence tools
- **Automation**: Automated report generation and distribution
