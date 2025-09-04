-- Surcharge vs Suppression Analysis
-- This query analyzes routing hint patterns for penalties and incentives

-- 1. Overall Surcharge/Suppression Summary (Last 30 Days)
SELECT 
    routing_hints.penalty_or_incentive,
    COUNT(*) as transaction_count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ()), 2) as percentage,
    ROUND(AVG(metadata->>'$.transaction_amount'), 2) as avg_transaction_amount,
    ROUND(SUM(CAST(metadata->>'$.transaction_amount' AS DECIMAL(10,2))), 2) as total_transaction_volume
FROM analytics_events,
JSON_TABLE(
    routing_hints,
    '$' COLUMNS(
        penalty_or_incentive VARCHAR(50) PATH '$.penalty_or_incentive'
    )
) as routing_hints
WHERE event_type = 'decision_outcome'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
    AND routing_hints IS NOT NULL
GROUP BY routing_hints.penalty_or_incentive
ORDER BY transaction_count DESC;

-- 2. Surcharge/Suppression by Decision Type (Last 30 Days)
SELECT 
    decision,
    routing_hints.penalty_or_incentive,
    COUNT(*) as transaction_count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY decision)), 2) as percentage_of_decision
FROM analytics_events,
JSON_TABLE(
    routing_hints,
    '$' COLUMNS(
        penalty_or_incentive VARCHAR(50) PATH '$.penalty_or_incentive'
    )
) as routing_hints
WHERE event_type = 'decision_outcome'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
    AND routing_hints IS NOT NULL
GROUP BY decision, routing_hints.penalty_or_incentive
ORDER BY decision, transaction_count DESC;

-- 3. Surcharge/Suppression by Transaction Amount Range (Last 30 Days)
SELECT 
    CASE 
        WHEN metadata->>'$.transaction_amount' IS NULL THEN 'Unknown'
        WHEN CAST(metadata->>'$.transaction_amount' AS DECIMAL(10,2)) < 50 THEN 'Under $50'
        WHEN CAST(metadata->>'$.transaction_amount' AS DECIMAL(10,2)) < 100 THEN '$50-$99'
        WHEN CAST(metadata->>'$.transaction_amount' AS DECIMAL(10,2)) < 500 THEN '$100-$499'
        WHEN CAST(metadata->>'$.transaction_amount' AS DECIMAL(10,2)) < 1000 THEN '$500-$999'
        ELSE 'Over $1000'
    END as amount_range,
    routing_hints.penalty_or_incentive,
    COUNT(*) as transaction_count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY amount_range)), 2) as percentage_of_range
FROM analytics_events,
JSON_TABLE(
    routing_hints,
    '$' COLUMNS(
        penalty_or_incentive VARCHAR(50) PATH '$.penalty_or_incentive'
    )
) as routing_hints
WHERE event_type = 'decision_outcome'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
    AND routing_hints IS NOT NULL
GROUP BY amount_range, routing_hints.penalty_or_incentive
ORDER BY 
    CASE amount_range
        WHEN 'Under $50' THEN 1
        WHEN '$50-$99' THEN 2
        WHEN '$100-$499' THEN 3
        WHEN '$500-$999' THEN 4
        WHEN 'Over $1000' THEN 5
        ELSE 6
    END, transaction_count DESC;

-- 4. Surcharge/Suppression by Merchant (Last 30 Days)
SELECT 
    merchant_id,
    routing_hints.penalty_or_incentive,
    COUNT(*) as transaction_count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY merchant_id)), 2) as percentage_of_merchant,
    ROUND(AVG(metadata->>'$.transaction_amount'), 2) as avg_transaction_amount
FROM analytics_events,
JSON_TABLE(
    routing_hints,
    '$' COLUMNS(
        penalty_or_incentive VARCHAR(50) PATH '$.penalty_or_incentive'
    )
) as routing_hints
WHERE event_type = 'decision_outcome'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
    AND routing_hints IS NOT NULL
GROUP BY merchant_id, routing_hints.penalty_or_incentive
HAVING transaction_count >= 5
ORDER BY merchant_id, transaction_count DESC;

-- 5. Surcharge/Suppression by Customer Segment (Last 30 Days)
SELECT 
    CASE 
        WHEN tags LIKE '%premium_customer%' THEN 'Premium'
        WHEN tags LIKE '%high_risk%' THEN 'High Risk'
        WHEN tags LIKE '%new_customer%' THEN 'New Customer'
        WHEN tags LIKE '%returning_customer%' THEN 'Returning Customer'
        ELSE 'Standard'
    END as customer_segment,
    routing_hints.penalty_or_incentive,
    COUNT(*) as transaction_count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY customer_segment)), 2) as percentage_of_segment
FROM analytics_events,
JSON_TABLE(
    routing_hints,
    '$' COLUMNS(
        penalty_or_incentive VARCHAR(50) PATH '$.penalty_or_incentive'
    )
) as routing_hints
WHERE event_type = 'decision_outcome'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
    AND routing_hints IS NOT NULL
GROUP BY customer_segment, routing_hints.penalty_or_incentive
ORDER BY customer_segment, transaction_count DESC;

-- 6. Surcharge/Suppression by Network Preference (Last 30 Days)
SELECT 
    routing_hints.preferred_network,
    routing_hints.penalty_or_incentive,
    COUNT(*) as transaction_count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY routing_hints.preferred_network)), 2) as percentage_of_network
FROM analytics_events,
JSON_TABLE(
    routing_hints,
    '$' COLUMNS(
        preferred_network VARCHAR(50) PATH '$.preferred_network',
        penalty_or_incentive VARCHAR(50) PATH '$.penalty_or_incentive'
    )
) as routing_hints
WHERE event_type = 'decision_outcome'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
    AND routing_hints IS NOT NULL
GROUP BY routing_hints.preferred_network, routing_hints.penalty_or_incentive
ORDER BY routing_hints.preferred_network, transaction_count DESC;

-- 7. Surcharge/Suppression by Acquirer (Last 30 Days)
SELECT 
    routing_hints.preferred_acquirer,
    routing_hints.penalty_or_incentive,
    COUNT(*) as transaction_count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY routing_hints.preferred_acquirer)), 2) as percentage_of_acquirer
FROM analytics_events,
JSON_TABLE(
    routing_hints,
    '$' COLUMNS(
        preferred_acquirer VARCHAR(100) PATH '$.preferred_acquirer',
        penalty_or_incentive VARCHAR(50) PATH '$.penalty_or_incentive'
    )
) as routing_hints
WHERE event_type = 'decision_outcome'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
    AND routing_hints IS NOT NULL
    AND routing_hints.preferred_acquirer IS NOT NULL
GROUP BY routing_hints.preferred_acquirer, routing_hints.penalty_or_incentive
ORDER BY routing_hints.preferred_acquirer, transaction_count DESC;

-- 8. Surcharge/Suppression by Business Rules (Last 30 Days)
SELECT 
    business_rules.rule_type,
    routing_hints.penalty_or_incentive,
    COUNT(*) as transaction_count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY business_rules.rule_type)), 2) as percentage_of_rule
FROM analytics_events,
JSON_TABLE(
    business_rules,
    '$[*]' COLUMNS(
        rule_type VARCHAR(100) PATH '$.rule_type'
    )
) as business_rules,
JSON_TABLE(
    routing_hints,
    '$' COLUMNS(
        penalty_or_incentive VARCHAR(50) PATH '$.penalty_or_incentive'
    )
) as routing_hints
WHERE event_type = 'decision_outcome'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
    AND business_rules IS NOT NULL
    AND routing_hints IS NOT NULL
GROUP BY business_rules.rule_type, routing_hints.penalty_or_incentive
ORDER BY business_rules.rule_type, transaction_count DESC;

-- 9. Surcharge/Suppression by Risk Level (Last 30 Days)
SELECT 
    CASE 
        WHEN decision = 'DECLINE' THEN 'High'
        WHEN decision = 'REVIEW' THEN 'Medium'
        WHEN decision = 'APPROVE' AND (confidence_score IS NULL OR confidence_score < 0.7) THEN 'Medium'
        WHEN decision = 'APPROVE' THEN 'Low'
        ELSE 'Unknown'
    END as risk_level,
    routing_hints.penalty_or_incentive,
    COUNT(*) as transaction_count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY risk_level)), 2) as percentage_of_risk_level
FROM analytics_events,
JSON_TABLE(
    routing_hints,
    '$' COLUMNS(
        penalty_or_incentive VARCHAR(50) PATH '$.penalty_or_incentive'
    )
) as routing_hints
WHERE event_type = 'decision_outcome'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
    AND routing_hints IS NOT NULL
GROUP BY risk_level, routing_hints.penalty_or_incentive
ORDER BY 
    CASE risk_level
        WHEN 'High' THEN 1
        WHEN 'Medium' THEN 2
        WHEN 'Low' THEN 3
        ELSE 4
    END, transaction_count DESC;

-- 10. Surcharge/Suppression by Time (Hourly - Last 7 Days)
SELECT 
    DATE_FORMAT(FROM_UNIXTIME(timestamp), '%Y-%m-%d %H:00:00') as hour_bucket,
    routing_hints.penalty_or_incentive,
    COUNT(*) as transaction_count
FROM analytics_events,
JSON_TABLE(
    routing_hints,
    '$' COLUMNS(
        penalty_or_incentive VARCHAR(50) PATH '$.penalty_or_incentive'
    )
) as routing_hints
WHERE event_type = 'decision_outcome'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 7 DAY))
    AND routing_hints IS NOT NULL
GROUP BY hour_bucket, routing_hints.penalty_or_incentive
ORDER BY hour_bucket, transaction_count DESC;

-- 11. Surcharge/Suppression by Time (Daily - Last 90 Days)
SELECT 
    DATE(FROM_UNIXTIME(timestamp)) as date_bucket,
    routing_hints.penalty_or_incentive,
    COUNT(*) as transaction_count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY date_bucket)), 2) as percentage_of_day
FROM analytics_events,
JSON_TABLE(
    routing_hints,
    '$' COLUMNS(
        penalty_or_incentive VARCHAR(50) PATH '$.penalty_or_incentive'
    )
) as routing_hints
WHERE event_type = 'decision_outcome'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 90 DAY))
    AND routing_hints IS NOT NULL
GROUP BY date_bucket, routing_hints.penalty_or_incentive
ORDER BY date_bucket, transaction_count DESC;

-- 12. Surcharge/Suppression by Week (Last 52 Weeks)
SELECT 
    YEARWEEK(FROM_UNIXTIME(timestamp)) as week_number,
    MIN(DATE(FROM_UNIXTIME(timestamp))) as week_start,
    routing_hints.penalty_or_incentive,
    COUNT(*) as transaction_count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY week_number)), 2) as percentage_of_week
FROM analytics_events,
JSON_TABLE(
    routing_hints,
    '$' COLUMNS(
        penalty_or_incentive VARCHAR(50) PATH '$.penalty_or_incentive'
    )
) as routing_hints
WHERE event_type = 'decision_outcome'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 52 WEEK))
    AND routing_hints IS NOT NULL
GROUP BY week_number, routing_hints.penalty_or_incentive
ORDER BY week_number, transaction_count DESC;

-- 13. Surcharge/Suppression by MCC Code (Last 30 Days)
SELECT 
    metadata->>'$.mcc_code' as mcc_code,
    routing_hints.penalty_or_incentive,
    COUNT(*) as transaction_count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY metadata->>'$.mcc_code')), 2) as percentage_of_mcc
FROM analytics_events,
JSON_TABLE(
    routing_hints,
    '$' COLUMNS(
        penalty_or_incentive VARCHAR(50) PATH '$.penalty_or_incentive'
    )
) as routing_hints
WHERE event_type = 'decision_outcome'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
    AND routing_hints IS NOT NULL
    AND metadata->>'$.mcc_code' IS NOT NULL
GROUP BY metadata->>'$.mcc_code', routing_hints.penalty_or_incentive
HAVING transaction_count >= 5
ORDER BY metadata->>'$.mcc_code', transaction_count DESC;

-- 14. Surcharge/Suppression by Confidence Score (Last 30 Days)
SELECT 
    CASE 
        WHEN confidence_score IS NULL THEN 'Unknown'
        WHEN confidence_score < 0.5 THEN 'Low (<50%)'
        WHEN confidence_score < 0.7 THEN 'Medium (50-70%)'
        WHEN confidence_score < 0.9 THEN 'High (70-90%)'
        ELSE 'Very High (>90%)'
    END as confidence_category,
    routing_hints.penalty_or_incentive,
    COUNT(*) as transaction_count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY confidence_category)), 2) as percentage_of_confidence
FROM analytics_events,
JSON_TABLE(
    routing_hints,
    '$' COLUMNS(
        penalty_or_incentive VARCHAR(50) PATH '$.penalty_or_incentive'
    )
) as routing_hints
WHERE event_type = 'decision_outcome'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
    AND routing_hints IS NOT NULL
GROUP BY confidence_category, routing_hints.penalty_or_incentive
ORDER BY 
    CASE confidence_category
        WHEN 'Low (<50%)' THEN 1
        WHEN 'Medium (50-70%)' THEN 2
        WHEN 'High (70-90%)' THEN 3
        WHEN 'Very High (>90%)' THEN 4
        ELSE 5
    END, transaction_count DESC;

-- 15. Surcharge/Suppression by Approval Odds (Last 30 Days)
SELECT 
    CASE 
        WHEN routing_hints.approval_odds IS NULL THEN 'Unknown'
        WHEN routing_hints.approval_odds < 0.3 THEN 'Low (<30%)'
        WHEN routing_hints.approval_odds < 0.6 THEN 'Medium (30-60%)'
        WHEN routing_hints.approval_odds < 0.8 THEN 'High (60-80%)'
        ELSE 'Very High (>80%)'
    END as approval_odds_category,
    routing_hints.penalty_or_incentive,
    COUNT(*) as transaction_count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY approval_odds_category)), 2) as percentage_of_odds
FROM analytics_events,
JSON_TABLE(
    routing_hints,
    '$' COLUMNS(
        penalty_or_incentive VARCHAR(50) PATH '$.penalty_or_incentive',
        approval_odds DECIMAL(5,4) PATH '$.approval_odds'
    )
) as routing_hints
WHERE event_type = 'decision_outcome'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
    AND routing_hints IS NOT NULL
GROUP BY approval_odds_category, routing_hints.penalty_or_incentive
ORDER BY 
    CASE approval_odds_category
        WHEN 'Low (<30%)' THEN 1
        WHEN 'Medium (30-60%)' THEN 2
        WHEN 'High (60-80%)' THEN 3
        WHEN 'Very High (>80%)' THEN 4
        ELSE 5
    END, transaction_count DESC;
