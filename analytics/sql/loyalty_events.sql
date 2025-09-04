-- Loyalty Events Analysis
-- This query analyzes loyalty events triggered by the decisioning system

-- 1. Overall Loyalty Events Summary (Last 30 Days)
SELECT 
    COUNT(*) as total_loyalty_events,
    COUNT(DISTINCT customer_id) as unique_customers,
    COUNT(DISTINCT merchant_id) as unique_merchants,
    ROUND(AVG(metadata->>'$.transaction_amount'), 2) as avg_transaction_amount,
    ROUND(SUM(CAST(metadata->>'$.transaction_amount' AS DECIMAL(10,2))), 2) as total_transaction_volume
FROM analytics_events 
WHERE event_type = 'loyalty_event'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY));

-- 2. Loyalty Events by Event Type (Last 30 Days)
SELECT 
    metadata->>'$.loyalty_event_type' as loyalty_event_type,
    COUNT(*) as event_count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ()), 2) as percentage,
    COUNT(DISTINCT customer_id) as unique_customers,
    ROUND(AVG(metadata->>'$.transaction_amount'), 2) as avg_transaction_amount
FROM analytics_events 
WHERE event_type = 'loyalty_event'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
    AND metadata->>'$.loyalty_event_type' IS NOT NULL
GROUP BY metadata->>'$.loyalty_event_type'
ORDER BY event_count DESC;

-- 3. Loyalty Events by Decision Type (Last 30 Days)
SELECT 
    decision,
    COUNT(*) as loyalty_event_count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY decision)), 2) as percentage_of_decision,
    COUNT(DISTINCT customer_id) as unique_customers
FROM analytics_events 
WHERE event_type = 'loyalty_event'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
GROUP BY decision
ORDER BY loyalty_event_count DESC;

-- 4. Loyalty Events by Customer Segment (Last 30 Days)
SELECT 
    CASE 
        WHEN tags LIKE '%premium_customer%' THEN 'Premium'
        WHEN tags LIKE '%high_risk%' THEN 'High Risk'
        WHEN tags LIKE '%new_customer%' THEN 'New Customer'
        WHEN tags LIKE '%returning_customer%' THEN 'Returning Customer'
        ELSE 'Standard'
    END as customer_segment,
    COUNT(*) as loyalty_event_count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ()), 2) as percentage,
    COUNT(DISTINCT customer_id) as unique_customers,
    ROUND(AVG(metadata->>'$.transaction_amount'), 2) as avg_transaction_amount
FROM analytics_events 
WHERE event_type = 'loyalty_event'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
GROUP BY customer_segment
ORDER BY loyalty_event_count DESC;

-- 5. Loyalty Events by Merchant (Last 30 Days)
SELECT 
    merchant_id,
    COUNT(*) as loyalty_event_count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ()), 2) as percentage,
    COUNT(DISTINCT customer_id) as unique_customers,
    ROUND(AVG(metadata->>'$.transaction_amount'), 2) as avg_transaction_amount
FROM analytics_events 
WHERE event_type = 'loyalty_event'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
GROUP BY merchant_id
HAVING loyalty_event_count >= 5
ORDER BY loyalty_event_count DESC;

-- 6. Loyalty Events by Transaction Amount Range (Last 30 Days)
SELECT 
    CASE 
        WHEN metadata->>'$.transaction_amount' IS NULL THEN 'Unknown'
        WHEN CAST(metadata->>'$.transaction_amount' AS DECIMAL(10,2)) < 50 THEN 'Under $50'
        WHEN CAST(metadata->>'$.transaction_amount' AS DECIMAL(10,2)) < 100 THEN '$50-$99'
        WHEN CAST(metadata->>'$.transaction_amount' AS DECIMAL(10,2)) < 500 THEN '$100-$499'
        WHEN CAST(metadata->>'$.transaction_amount' AS DECIMAL(10,2)) < 1000 THEN '$500-$999'
        ELSE 'Over $1000'
    END as amount_range,
    COUNT(*) as loyalty_event_count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ()), 2) as percentage,
    COUNT(DISTINCT customer_id) as unique_customers
FROM analytics_events 
WHERE event_type = 'loyalty_event'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
GROUP BY amount_range
ORDER BY 
    CASE amount_range
        WHEN 'Under $50' THEN 1
        WHEN '$50-$99' THEN 2
        WHEN '$100-$499' THEN 3
        WHEN '$500-$999' THEN 4
        WHEN 'Over $1000' THEN 5
        ELSE 6
    END;

-- 7. Loyalty Events by Business Rules (Last 30 Days)
SELECT 
    business_rules.rule_type,
    COUNT(*) as loyalty_event_count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ()), 2) as percentage,
    COUNT(DISTINCT customer_id) as unique_customers
FROM analytics_events,
JSON_TABLE(
    business_rules,
    '$[*]' COLUMNS(
        rule_type VARCHAR(100) PATH '$.rule_type'
    )
) as business_rules
WHERE event_type = 'loyalty_event'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
    AND business_rules IS NOT NULL
GROUP BY business_rules.rule_type
ORDER BY loyalty_event_count DESC;

-- 8. Loyalty Events by Time (Hourly - Last 7 Days)
SELECT 
    DATE_FORMAT(FROM_UNIXTIME(timestamp), '%Y-%m-%d %H:00:00') as hour_bucket,
    COUNT(*) as loyalty_event_count,
    COUNT(DISTINCT customer_id) as unique_customers
FROM analytics_events 
WHERE event_type = 'loyalty_event'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 7 DAY))
GROUP BY hour_bucket
ORDER BY hour_bucket;

-- 9. Loyalty Events by Time (Daily - Last 90 Days)
SELECT 
    DATE(FROM_UNIXTIME(timestamp)) as date_bucket,
    COUNT(*) as loyalty_event_count,
    COUNT(DISTINCT customer_id) as unique_customers,
    ROUND(AVG(metadata->>'$.transaction_amount'), 2) as avg_transaction_amount
FROM analytics_events 
WHERE event_type = 'loyalty_event'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 90 DAY))
GROUP BY date_bucket
ORDER BY date_bucket;

-- 10. Loyalty Events by Week (Last 52 Weeks)
SELECT 
    YEARWEEK(FROM_UNIXTIME(timestamp)) as week_number,
    MIN(DATE(FROM_UNIXTIME(timestamp))) as week_start,
    COUNT(*) as loyalty_event_count,
    COUNT(DISTINCT customer_id) as unique_customers,
    ROUND(AVG(metadata->>'$.transaction_amount'), 2) as avg_transaction_amount
FROM analytics_events 
WHERE event_type = 'loyalty_event'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 52 WEEK))
GROUP BY week_number
ORDER BY week_number;

-- 11. Loyalty Events by MCC Code (Last 30 Days)
SELECT 
    metadata->>'$.mcc_code' as mcc_code,
    COUNT(*) as loyalty_event_count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ()), 2) as percentage,
    COUNT(DISTINCT customer_id) as unique_customers,
    ROUND(AVG(metadata->>'$.transaction_amount'), 2) as avg_transaction_amount
FROM analytics_events 
WHERE event_type = 'loyalty_event'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
    AND metadata->>'$.mcc_code' IS NOT NULL
GROUP BY metadata->>'$.mcc_code'
HAVING loyalty_event_count >= 3
ORDER BY loyalty_event_count DESC;

-- 12. Loyalty Events by Confidence Score (Last 30 Days)
SELECT 
    CASE 
        WHEN confidence_score IS NULL THEN 'Unknown'
        WHEN confidence_score < 0.5 THEN 'Low (<50%)'
        WHEN confidence_score < 0.7 THEN 'Medium (50-70%)'
        WHEN confidence_score < 0.9 THEN 'High (70-90%)'
        ELSE 'Very High (>90%)'
    END as confidence_category,
    COUNT(*) as loyalty_event_count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ()), 2) as percentage,
    COUNT(DISTINCT customer_id) as unique_customers
FROM analytics_events 
WHERE event_type = 'loyalty_event'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
GROUP BY confidence_category
ORDER BY 
    CASE confidence_category
        WHEN 'Low (<50%)' THEN 1
        WHEN 'Medium (50-70%)' THEN 2
        WHEN 'High (70-90%)' THEN 3
        WHEN 'Very High (>90%)' THEN 4
        ELSE 5
    END;

-- 13. Loyalty Events by Risk Level (Last 30 Days)
SELECT 
    CASE 
        WHEN decision = 'DECLINE' THEN 'High'
        WHEN decision = 'REVIEW' THEN 'Medium'
        WHEN decision = 'APPROVE' AND (confidence_score IS NULL OR confidence_score < 0.7) THEN 'Medium'
        WHEN decision = 'APPROVE' THEN 'Low'
        ELSE 'Unknown'
    END as risk_level,
    COUNT(*) as loyalty_event_count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ()), 2) as percentage,
    COUNT(DISTINCT customer_id) as unique_customers
FROM analytics_events 
WHERE event_type = 'loyalty_event'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
GROUP BY risk_level
ORDER BY 
    CASE risk_level
        WHEN 'High' THEN 1
        WHEN 'Medium' THEN 2
        WHEN 'Low' THEN 3
        ELSE 4
    END;

-- 14. Loyalty Events by Routing Hints (Last 30 Days)
SELECT 
    routing_hints.preferred_network,
    routing_hints.penalty_or_incentive,
    COUNT(*) as loyalty_event_count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ()), 2) as percentage,
    COUNT(DISTINCT customer_id) as unique_customers
FROM analytics_events,
JSON_TABLE(
    routing_hints,
    '$' COLUMNS(
        preferred_network VARCHAR(50) PATH '$.preferred_network',
        penalty_or_incentive VARCHAR(50) PATH '$.penalty_or_incentive'
    )
) as routing_hints
WHERE event_type = 'loyalty_event'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
    AND routing_hints IS NOT NULL
GROUP BY routing_hints.preferred_network, routing_hints.penalty_or_incentive
ORDER BY loyalty_event_count DESC;

-- 15. Customer Loyalty Engagement (Last 30 Days)
SELECT 
    customer_id,
    COUNT(*) as loyalty_event_count,
    COUNT(DISTINCT merchant_id) as unique_merchants,
    ROUND(AVG(metadata->>'$.transaction_amount'), 2) as avg_transaction_amount,
    ROUND(SUM(CAST(metadata->>'$.transaction_amount' AS DECIMAL(10,2))), 2) as total_transaction_volume,
    MIN(FROM_UNIXTIME(timestamp)) as first_loyalty_event,
    MAX(FROM_UNIXTIME(timestamp)) as last_loyalty_event
FROM analytics_events 
WHERE event_type = 'loyalty_event'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
GROUP BY customer_id
HAVING loyalty_event_count >= 2
ORDER BY loyalty_event_count DESC;

-- 16. Loyalty Events by Error Flags (Last 30 Days)
SELECT 
    error_flags.error_code,
    error_flags.error_message,
    error_flags.severity,
    COUNT(*) as loyalty_event_count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ()), 2) as percentage
FROM analytics_events,
JSON_TABLE(
    error_flags,
    '$[*]' COLUMNS(
        error_code VARCHAR(100) PATH '$.error_code',
        error_message VARCHAR(500) PATH '$.error_message',
        severity VARCHAR(50) PATH '$.severity'
    )
) as error_flags
WHERE event_type = 'loyalty_event'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
    AND error_flags IS NOT NULL
GROUP BY error_flags.error_code, error_flags.error_message, error_flags.severity
ORDER BY loyalty_event_count DESC;

-- 17. Loyalty Events Performance Metrics (Last 30 Days)
SELECT 
    CASE 
        WHEN performance_metrics.total_latency_ms < 100 THEN 'Fast (<100ms)'
        WHEN performance_metrics.total_latency_ms < 500 THEN 'Normal (100-500ms)'
        WHEN performance_metrics.total_latency_ms < 1000 THEN 'Slow (500-1000ms)'
        ELSE 'Very Slow (>1000ms)'
    END as performance_category,
    COUNT(*) as loyalty_event_count,
    ROUND(AVG(performance_metrics.total_latency_ms), 2) as avg_total_latency_ms,
    ROUND(AVG(performance_metrics.scoring_latency_ms), 2) as avg_scoring_latency_ms,
    ROUND(AVG(performance_metrics.routing_latency_ms), 2) as avg_routing_latency_ms
FROM analytics_events 
WHERE event_type = 'loyalty_event'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
    AND performance_metrics IS NOT NULL
GROUP BY performance_category
ORDER BY 
    CASE performance_category
        WHEN 'Fast (<100ms)' THEN 1
        WHEN 'Normal (100-500ms)' THEN 2
        WHEN 'Slow (500-1000ms)' THEN 3
        WHEN 'Very Slow (>1000ms)' THEN 4
    END;

-- 18. Loyalty Events by Tags (Last 30 Days)
SELECT 
    CASE 
        WHEN tags LIKE '%loyalty_boost%' THEN 'Loyalty Boost Applied'
        WHEN tags LIKE '%loyalty_suppression%' THEN 'Loyalty Suppression'
        WHEN tags LIKE '%loyalty_verification%' THEN 'Loyalty Verification Required'
        WHEN tags LIKE '%loyalty_expiry%' THEN 'Loyalty Expiry Warning'
        WHEN tags LIKE '%loyalty_upgrade%' THEN 'Loyalty Upgrade Opportunity'
        ELSE 'Standard Loyalty Event'
    END as loyalty_tag_category,
    COUNT(*) as loyalty_event_count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ()), 2) as percentage,
    COUNT(DISTINCT customer_id) as unique_customers
FROM analytics_events 
WHERE event_type = 'loyalty_event'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
GROUP BY loyalty_tag_category
ORDER BY loyalty_event_count DESC;

-- 19. Loyalty Events by Geographic Region (Last 30 Days)
SELECT 
    metadata->>'$.geographic_region' as geographic_region,
    COUNT(*) as loyalty_event_count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ()), 2) as percentage,
    COUNT(DISTINCT customer_id) as unique_customers,
    ROUND(AVG(metadata->>'$.transaction_amount'), 2) as avg_transaction_amount
FROM analytics_events 
WHERE event_type = 'loyalty_event'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
    AND metadata->>'$.geographic_region' IS NOT NULL
GROUP BY metadata->>'$.geographic_region'
HAVING loyalty_event_count >= 3
ORDER BY loyalty_event_count DESC;

-- 20. Loyalty Events Trend Analysis (Last 12 Months)
SELECT 
    DATE_FORMAT(FROM_UNIXTIME(timestamp), '%Y-%m') as month_bucket,
    COUNT(*) as loyalty_event_count,
    COUNT(DISTINCT customer_id) as unique_customers,
    ROUND(AVG(metadata->>'$.transaction_amount'), 2) as avg_transaction_amount,
    ROUND(SUM(CAST(metadata->>'$.transaction_amount' AS DECIMAL(10,2))), 2) as total_transaction_volume,
    LAG(COUNT(*)) OVER (ORDER BY month_bucket) as prev_month_count,
    ROUND(
        ((COUNT(*) - LAG(COUNT(*)) OVER (ORDER BY month_bucket)) * 100.0 / LAG(COUNT(*)) OVER (ORDER BY month_bucket)), 
        2
    ) as month_over_month_change_percent
FROM analytics_events 
WHERE event_type = 'loyalty_event'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 12 MONTH))
GROUP BY month_bucket
ORDER BY month_bucket;
