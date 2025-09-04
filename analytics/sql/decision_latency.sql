-- Decision Latency Analysis
-- This query analyzes processing time for transaction decisions

-- 1. Overall Performance Summary (Last 30 Days)
SELECT 
    COUNT(*) as total_transactions,
    ROUND(AVG(performance_metrics.total_latency_ms), 2) as avg_total_latency_ms,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY performance_metrics.total_latency_ms), 2) as median_total_latency_ms,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY performance_metrics.total_latency_ms), 2) as p95_total_latency_ms,
    ROUND(PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY performance_metrics.total_latency_ms), 2) as p99_total_latency_ms,
    ROUND(MIN(performance_metrics.total_latency_ms), 2) as min_total_latency_ms,
    ROUND(MAX(performance_metrics.total_latency_ms), 2) as max_total_latency_ms
FROM analytics_events 
WHERE event_type = 'decision_outcome'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
    AND performance_metrics IS NOT NULL;

-- 2. Performance by Decision Type (Last 30 Days)
SELECT 
    decision,
    COUNT(*) as transaction_count,
    ROUND(AVG(performance_metrics.total_latency_ms), 2) as avg_total_latency_ms,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY performance_metrics.total_latency_ms), 2) as p95_total_latency_ms,
    ROUND(MIN(performance_metrics.total_latency_ms), 2) as min_total_latency_ms,
    ROUND(MAX(performance_metrics.total_latency_ms), 2) as max_total_latency_ms
FROM analytics_events 
WHERE event_type = 'decision_outcome'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
    AND performance_metrics IS NOT NULL
GROUP BY decision
ORDER BY avg_total_latency_ms DESC;

-- 3. Performance by Processing Time Category (Last 30 Days)
SELECT 
    CASE 
        WHEN performance_metrics.total_latency_ms < 100 THEN 'Fast (<100ms)'
        WHEN performance_metrics.total_latency_ms < 500 THEN 'Normal (100-500ms)'
        WHEN performance_metrics.total_latency_ms < 1000 THEN 'Slow (500-1000ms)'
        ELSE 'Very Slow (>1000ms)'
    END as performance_category,
    COUNT(*) as transaction_count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ()), 2) as percentage
FROM analytics_events 
WHERE event_type = 'decision_outcome'
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

-- 4. Performance by Component (Last 30 Days)
SELECT 
    'Scoring' as component,
    COUNT(*) as transaction_count,
    ROUND(AVG(performance_metrics.scoring_latency_ms), 2) as avg_latency_ms,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY performance_metrics.scoring_latency_ms), 2) as p95_latency_ms
FROM analytics_events 
WHERE event_type = 'decision_outcome'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
    AND performance_metrics IS NOT NULL
    AND performance_metrics.scoring_latency_ms > 0

UNION ALL

SELECT 
    'Routing' as component,
    COUNT(*) as transaction_count,
    ROUND(AVG(performance_metrics.routing_latency_ms), 2) as avg_latency_ms,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY performance_metrics.routing_latency_ms), 2) as p95_latency_ms
FROM analytics_events 
WHERE event_type = 'decision_outcome'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
    AND performance_metrics IS NOT NULL
    AND performance_metrics.routing_latency_ms > 0

UNION ALL

SELECT 
    'Decision Logic' as component,
    COUNT(*) as transaction_count,
    ROUND(AVG(performance_metrics.decision_latency_ms), 2) as avg_latency_ms,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY performance_metrics.decision_latency_ms), 2) as p95_latency_ms
FROM analytics_events 
WHERE event_type = 'decision_outcome'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
    AND performance_metrics IS NOT NULL
    AND performance_metrics.decision_latency_ms > 0

UNION ALL

SELECT 
    'External APIs' as component,
    COUNT(*) as transaction_count,
    ROUND(AVG(performance_metrics.external_api_latency_ms), 2) as avg_latency_ms,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY performance_metrics.external_api_latency_ms), 2) as p95_latency_ms
FROM analytics_events 
WHERE event_type = 'decision_outcome'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
    AND performance_metrics IS NOT NULL
    AND performance_metrics.external_api_latency_ms > 0;

-- 5. Performance by Time (Hourly - Last 7 Days)
SELECT 
    DATE_FORMAT(FROM_UNIXTIME(timestamp), '%Y-%m-%d %H:00:00') as hour_bucket,
    COUNT(*) as transaction_count,
    ROUND(AVG(performance_metrics.total_latency_ms), 2) as avg_total_latency_ms,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY performance_metrics.total_latency_ms), 2) as p95_total_latency_ms
FROM analytics_events 
WHERE event_type = 'decision_outcome'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 7 DAY))
    AND performance_metrics IS NOT NULL
GROUP BY hour_bucket
ORDER BY hour_bucket;

-- 6. Performance by Time (Daily - Last 90 Days)
SELECT 
    DATE(FROM_UNIXTIME(timestamp)) as date_bucket,
    COUNT(*) as transaction_count,
    ROUND(AVG(performance_metrics.total_latency_ms), 2) as avg_total_latency_ms,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY performance_metrics.total_latency_ms), 2) as p95_total_latency_ms,
    ROUND(MIN(performance_metrics.total_latency_ms), 2) as min_total_latency_ms,
    ROUND(MAX(performance_metrics.total_latency_ms), 2) as max_total_latency_ms
FROM analytics_events 
WHERE event_type = 'decision_outcome'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 90 DAY))
    AND performance_metrics IS NOT NULL
GROUP BY date_bucket
ORDER BY date_bucket;

-- 7. Performance by Merchant (Last 30 Days)
SELECT 
    merchant_id,
    COUNT(*) as transaction_count,
    ROUND(AVG(performance_metrics.total_latency_ms), 2) as avg_total_latency_ms,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY performance_metrics.total_latency_ms), 2) as p95_total_latency_ms
FROM analytics_events 
WHERE event_type = 'decision_outcome'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
    AND performance_metrics IS NOT NULL
GROUP BY merchant_id
HAVING transaction_count >= 10
ORDER BY avg_total_latency_ms DESC;

-- 8. Performance by Transaction Amount Range (Last 30 Days)
SELECT 
    CASE 
        WHEN metadata->>'$.transaction_amount' IS NULL THEN 'Unknown'
        WHEN CAST(metadata->>'$.transaction_amount' AS DECIMAL(10,2)) < 50 THEN 'Under $50'
        WHEN CAST(metadata->>'$.transaction_amount' AS DECIMAL(10,2)) < 100 THEN '$50-$99'
        WHEN CAST(metadata->>'$.transaction_amount' AS DECIMAL(10,2)) < 500 THEN '$100-$499'
        WHEN CAST(metadata->>'$.transaction_amount' AS DECIMAL(10,2)) < 1000 THEN '$500-$999'
        ELSE 'Over $1000'
    END as amount_range,
    COUNT(*) as transaction_count,
    ROUND(AVG(performance_metrics.total_latency_ms), 2) as avg_total_latency_ms,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY performance_metrics.total_latency_ms), 2) as p95_total_latency_ms
FROM analytics_events 
WHERE event_type = 'decision_outcome'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
    AND performance_metrics IS NOT NULL
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

-- 9. Performance by External API Calls (Last 30 Days)
SELECT 
    performance_metrics.external_api_calls,
    COUNT(*) as transaction_count,
    ROUND(AVG(performance_metrics.total_latency_ms), 2) as avg_total_latency_ms,
    ROUND(AVG(performance_metrics.external_api_latency_ms), 2) as avg_api_latency_ms,
    ROUND((performance_metrics.external_api_latency_ms * 100.0 / performance_metrics.total_latency_ms), 2) as api_latency_percentage
FROM analytics_events 
WHERE event_type = 'decision_outcome'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
    AND performance_metrics IS NOT NULL
    AND performance_metrics.external_api_calls > 0
GROUP BY performance_metrics.external_api_calls
ORDER BY performance_metrics.external_api_calls;

-- 10. Performance by Business Rules Applied (Last 30 Days)
SELECT 
    business_rules.rule_type,
    COUNT(*) as rule_applied_count,
    ROUND(AVG(performance_metrics.total_latency_ms), 2) as avg_total_latency_ms,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY performance_metrics.total_latency_ms), 2) as p95_total_latency_ms
FROM analytics_events,
JSON_TABLE(
    business_rules,
    '$[*]' COLUMNS(
        rule_type VARCHAR(100) PATH '$.rule_type'
    )
) as business_rules
WHERE event_type = 'decision_outcome'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
    AND performance_metrics IS NOT NULL
    AND business_rules IS NOT NULL
GROUP BY business_rules.rule_type
ORDER BY avg_total_latency_ms DESC;

-- 11. Performance by Customer Segment (Last 30 Days)
SELECT 
    CASE 
        WHEN tags LIKE '%premium_customer%' THEN 'Premium'
        WHEN tags LIKE '%high_risk%' THEN 'High Risk'
        WHEN tags LIKE '%new_customer%' THEN 'New Customer'
        WHEN tags LIKE '%returning_customer%' THEN 'Returning Customer'
        ELSE 'Standard'
    END as customer_segment,
    COUNT(*) as transaction_count,
    ROUND(AVG(performance_metrics.total_latency_ms), 2) as avg_total_latency_ms,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY performance_metrics.total_latency_ms), 2) as p95_total_latency_ms
FROM analytics_events 
WHERE event_type = 'decision_outcome'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
    AND performance_metrics IS NOT NULL
GROUP BY customer_segment
ORDER BY avg_total_latency_ms DESC;

-- 12. Performance Trend by Week (Last 52 Weeks)
SELECT 
    YEARWEEK(FROM_UNIXTIME(timestamp)) as week_number,
    MIN(DATE(FROM_UNIXTIME(timestamp))) as week_start,
    COUNT(*) as transaction_count,
    ROUND(AVG(performance_metrics.total_latency_ms), 2) as avg_total_latency_ms,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY performance_metrics.total_latency_ms), 2) as p95_total_latency_ms
FROM analytics_events 
WHERE event_type = 'decision_outcome'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 52 WEEK))
    AND performance_metrics IS NOT NULL
GROUP BY week_number
ORDER BY week_number;

-- 13. Performance by Memory Usage (Last 30 Days)
SELECT 
    CASE 
        WHEN performance_metrics.memory_usage_mb IS NULL THEN 'Unknown'
        WHEN performance_metrics.memory_usage_mb < 100 THEN 'Low (<100MB)'
        WHEN performance_metrics.memory_usage_mb < 200 THEN 'Medium (100-200MB)'
        WHEN performance_metrics.memory_usage_mb < 500 THEN 'High (200-500MB)'
        ELSE 'Very High (>500MB)'
    END as memory_usage_category,
    COUNT(*) as transaction_count,
    ROUND(AVG(performance_metrics.total_latency_ms), 2) as avg_total_latency_ms,
    ROUND(AVG(performance_metrics.memory_usage_mb), 2) as avg_memory_usage_mb
FROM analytics_events 
WHERE event_type = 'decision_outcome'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
    AND performance_metrics IS NOT NULL
    AND performance_metrics.memory_usage_mb IS NOT NULL
GROUP BY memory_usage_category
ORDER BY 
    CASE memory_usage_category
        WHEN 'Low (<100MB)' THEN 1
        WHEN 'Medium (100-200MB)' THEN 2
        WHEN 'High (200-500MB)' THEN 3
        WHEN 'Very High (>500MB)' THEN 4
        ELSE 5
    END;

-- 14. Performance by CPU Usage (Last 30 Days)
SELECT 
    CASE 
        WHEN performance_metrics.cpu_usage_percent IS NULL THEN 'Unknown'
        WHEN performance_metrics.cpu_usage_percent < 25 THEN 'Low (<25%)'
        WHEN performance_metrics.cpu_usage_percent < 50 THEN 'Medium (25-50%)'
        WHEN performance_metrics.cpu_usage_percent < 75 THEN 'High (50-75%)'
        ELSE 'Very High (>75%)'
    END as cpu_usage_category,
    COUNT(*) as transaction_count,
    ROUND(AVG(performance_metrics.total_latency_ms), 2) as avg_total_latency_ms,
    ROUND(AVG(performance_metrics.cpu_usage_percent), 2) as avg_cpu_usage_percent
FROM analytics_events 
WHERE event_type = 'decision_outcome'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
    AND performance_metrics IS NOT NULL
    AND performance_metrics.cpu_usage_percent IS NOT NULL
GROUP BY cpu_usage_category
ORDER BY 
    CASE cpu_usage_category
        WHEN 'Low (<25%)' THEN 1
        WHEN 'Medium (25-50%)' THEN 2
        WHEN 'High (50-75%)' THEN 3
        WHEN 'Very High (>75%)' THEN 4
        ELSE 5
    END;
