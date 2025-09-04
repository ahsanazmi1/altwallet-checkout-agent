-- Approval Rate Analysis
-- This query analyzes transaction approval rates across multiple dimensions

-- 1. Overall Approval Rate (Last 30 Days)
SELECT 
    COUNT(*) as total_transactions,
    SUM(CASE WHEN decision = 'APPROVE' THEN 1 ELSE 0 END) as approved_transactions,
    SUM(CASE WHEN decision = 'DECLINE' THEN 1 ELSE 0 END) as declined_transactions,
    SUM(CASE WHEN decision = 'REVIEW' THEN 1 ELSE 0 END) as review_transactions,
    ROUND(
        (SUM(CASE WHEN decision = 'APPROVE' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 
        2
    ) as approval_rate_percent,
    ROUND(
        (SUM(CASE WHEN decision = 'DECLINE' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 
        2
    ) as decline_rate_percent,
    ROUND(
        (SUM(CASE WHEN decision = 'REVIEW' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 
        2
    ) as review_rate_percent
FROM analytics_events 
WHERE event_type = 'decision_outcome'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY));

-- 2. Approval Rate by Merchant (Last 30 Days)
SELECT 
    merchant_id,
    COUNT(*) as total_transactions,
    SUM(CASE WHEN decision = 'APPROVE' THEN 1 ELSE 0 END) as approved_transactions,
    ROUND(
        (SUM(CASE WHEN decision = 'APPROVE' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 
        2
    ) as approval_rate_percent,
    ROUND(
        (SUM(CASE WHEN decision = 'DECLINE' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 
        2
    ) as decline_rate_percent,
    ROUND(
        (SUM(CASE WHEN decision = 'REVIEW' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 
        2
    ) as review_rate_percent
FROM analytics_events 
WHERE event_type = 'decision_outcome'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
GROUP BY merchant_id
ORDER BY total_transactions DESC;

-- 3. Approval Rate by Time (Hourly - Last 7 Days)
SELECT 
    DATE_FORMAT(FROM_UNIXTIME(timestamp), '%Y-%m-%d %H:00:00') as hour_bucket,
    COUNT(*) as total_transactions,
    SUM(CASE WHEN decision = 'APPROVE' THEN 1 ELSE 0 END) as approved_transactions,
    ROUND(
        (SUM(CASE WHEN decision = 'APPROVE' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 
        2
    ) as approval_rate_percent
FROM analytics_events 
WHERE event_type = 'decision_outcome'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 7 DAY))
GROUP BY hour_bucket
ORDER BY hour_bucket;

-- 4. Approval Rate by Time (Daily - Last 90 Days)
SELECT 
    DATE(FROM_UNIXTIME(timestamp)) as date_bucket,
    COUNT(*) as total_transactions,
    SUM(CASE WHEN decision = 'APPROVE' THEN 1 ELSE 0 END) as approved_transactions,
    ROUND(
        (SUM(CASE WHEN decision = 'APPROVE' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 
        2
    ) as approval_rate_percent,
    ROUND(
        (SUM(CASE WHEN decision = 'DECLINE' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 
        2
    ) as decline_rate_percent
FROM analytics_events 
WHERE event_type = 'decision_outcome'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 90 DAY))
GROUP BY date_bucket
ORDER BY date_bucket;

-- 5. Approval Rate by Transaction Amount Range (Last 30 Days)
SELECT 
    CASE 
        WHEN metadata->>'$.transaction_amount' IS NULL THEN 'Unknown'
        WHEN CAST(metadata->>'$.transaction_amount' AS DECIMAL(10,2)) < 50 THEN 'Under $50'
        WHEN CAST(metadata->>'$.transaction_amount' AS DECIMAL(10,2)) < 100 THEN '$50-$99'
        WHEN CAST(metadata->>'$.transaction_amount' AS DECIMAL(10,2)) < 500 THEN '$100-$499'
        WHEN CAST(metadata->>'$.transaction_amount' AS DECIMAL(10,2)) < 1000 THEN '$500-$999'
        ELSE 'Over $1000'
    END as amount_range,
    COUNT(*) as total_transactions,
    SUM(CASE WHEN decision = 'APPROVE' THEN 1 ELSE 0 END) as approved_transactions,
    ROUND(
        (SUM(CASE WHEN decision = 'APPROVE' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 
        2
    ) as approval_rate_percent
FROM analytics_events 
WHERE event_type = 'decision_outcome'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
    AND metadata->>'$.transaction_amount' IS NOT NULL
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

-- 6. Approval Rate by Customer Segment (Last 30 Days)
SELECT 
    CASE 
        WHEN tags LIKE '%premium_customer%' THEN 'Premium'
        WHEN tags LIKE '%high_risk%' THEN 'High Risk'
        WHEN tags LIKE '%new_customer%' THEN 'New Customer'
        WHEN tags LIKE '%returning_customer%' THEN 'Returning Customer'
        ELSE 'Standard'
    END as customer_segment,
    COUNT(*) as total_transactions,
    SUM(CASE WHEN decision = 'APPROVE' THEN 1 ELSE 0 END) as approved_transactions,
    ROUND(
        (SUM(CASE WHEN decision = 'APPROVE' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 
        2
    ) as approval_rate_percent
FROM analytics_events 
WHERE event_type = 'decision_outcome'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
GROUP BY customer_segment
ORDER BY approval_rate_percent DESC;

-- 7. Approval Rate Trend by Week (Last 52 Weeks)
SELECT 
    YEARWEEK(FROM_UNIXTIME(timestamp)) as week_number,
    MIN(DATE(FROM_UNIXTIME(timestamp))) as week_start,
    COUNT(*) as total_transactions,
    SUM(CASE WHEN decision = 'APPROVE' THEN 1 ELSE 0 END) as approved_transactions,
    ROUND(
        (SUM(CASE WHEN decision = 'APPROVE' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 
        2
    ) as approval_rate_percent
FROM analytics_events 
WHERE event_type = 'decision_outcome'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 52 WEEK))
GROUP BY week_number
ORDER BY week_number;

-- 8. Approval Rate by Business Rules Applied (Last 30 Days)
SELECT 
    business_rules.rule_type,
    business_rules.rule_name,
    COUNT(*) as total_applications,
    SUM(CASE WHEN decision = 'APPROVE' THEN 1 ELSE 0 END) as approved_with_rule,
    ROUND(
        (SUM(CASE WHEN decision = 'APPROVE' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 
        2
    ) as approval_rate_with_rule,
    ROUND(AVG(business_rules.impact_score), 3) as avg_impact_score
FROM analytics_events,
JSON_TABLE(
    business_rules,
    '$[*]' COLUMNS(
        rule_type VARCHAR(100) PATH '$.rule_type',
        rule_name VARCHAR(200) PATH '$.rule_name',
        impact_score DECIMAL(5,3) PATH '$.impact_score'
    )
) as business_rules
WHERE event_type = 'decision_outcome'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
    AND business_rules IS NOT NULL
GROUP BY business_rules.rule_type, business_rules.rule_name
ORDER BY total_applications DESC;
