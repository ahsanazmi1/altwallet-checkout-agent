-- Decline Reasons Analysis
-- This query analyzes the distribution of decline reasons and fraud indicators

-- 1. Overall Decline Distribution (Last 30 Days)
SELECT 
    decision,
    COUNT(*) as transaction_count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ()), 2) as percentage
FROM analytics_events 
WHERE event_type = 'decision_outcome'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
GROUP BY decision
ORDER BY transaction_count DESC;

-- 2. Decline Reasons by Error Flags (Last 30 Days)
SELECT 
    error_flags.error_code,
    error_flags.error_message,
    error_flags.severity,
    error_flags.component,
    COUNT(*) as occurrence_count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ()), 2) as percentage
FROM analytics_events,
JSON_TABLE(
    error_flags,
    '$[*]' COLUMNS(
        error_code VARCHAR(100) PATH '$.error_code',
        error_message VARCHAR(500) PATH '$.error_message',
        severity VARCHAR(50) PATH '$.severity',
        component VARCHAR(100) PATH '$.component'
    )
) as error_flags
WHERE event_type = 'decision_outcome'
    AND decision = 'DECLINE'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
    AND error_flags IS NOT NULL
GROUP BY error_flags.error_code, error_flags.error_message, error_flags.severity, error_flags.component
ORDER BY occurrence_count DESC;

-- 3. Decline Reasons by Risk Factors (Last 30 Days)
SELECT 
    risk_factor,
    COUNT(*) as occurrence_count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ()), 2) as percentage
FROM analytics_events,
JSON_TABLE(
    metadata->>'$.risk_factors',
    '$[*]' COLUMNS(
        risk_factor VARCHAR(100) PATH '$'
    )
) as risk_factors
WHERE event_type = 'decision_outcome'
    AND decision = 'DECLINE'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
    AND metadata->>'$.risk_factors' IS NOT NULL
GROUP BY risk_factor
ORDER BY occurrence_count DESC;

-- 4. Decline Reasons by Fraud Indicators (Last 30 Days)
SELECT 
    fraud_indicator,
    COUNT(*) as occurrence_count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ()), 2) as percentage
FROM analytics_events,
JSON_TABLE(
    metadata->>'$.fraud_indicators',
    '$[*]' COLUMNS(
        fraud_indicator VARCHAR(100) PATH '$'
    )
) as fraud_indicators
WHERE event_type = 'decision_outcome'
    AND decision = 'DECLINE'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
    AND metadata->>'$.fraud_indicators' IS NOT NULL
GROUP BY fraud_indicator
ORDER BY occurrence_count DESC;

-- 5. Decline Reasons by Compliance Flags (Last 30 Days)
SELECT 
    compliance_flag,
    COUNT(*) as occurrence_count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ()), 2) as percentage
FROM analytics_events,
JSON_TABLE(
    metadata->>'$.compliance_flags',
    '$[*]' COLUMNS(
        compliance_flag VARCHAR(100) PATH '$'
    )
) as compliance_flags
WHERE event_type = 'decision_outcome'
    AND decision = 'DECLINE'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
    AND metadata->>'$.compliance_flags' IS NOT NULL
GROUP BY compliance_flag
ORDER BY occurrence_count DESC;

-- 6. Decline Reasons by Business Rules (Last 30 Days)
SELECT 
    business_rules.rule_type,
    business_rules.rule_name,
    COUNT(*) as rule_triggered_count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ()), 2) as percentage,
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
    AND decision = 'DECLINE'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
    AND business_rules IS NOT NULL
GROUP BY business_rules.rule_type, business_rules.rule_name
ORDER BY rule_triggered_count DESC;

-- 7. Decline Reasons by Transaction Amount Range (Last 30 Days)
SELECT 
    CASE 
        WHEN metadata->>'$.transaction_amount' IS NULL THEN 'Unknown'
        WHEN CAST(metadata->>'$.transaction_amount' AS DECIMAL(10,2)) < 50 THEN 'Under $50'
        WHEN CAST(metadata->>'$.transaction_amount' AS DECIMAL(10,2)) < 100 THEN '$50-$99'
        WHEN CAST(metadata->>'$.transaction_amount' AS DECIMAL(10,2)) < 500 THEN '$100-$499'
        WHEN CAST(metadata->>'$.transaction_amount' AS DECIMAL(10,2)) < 1000 THEN '$500-$999'
        ELSE 'Over $1000'
    END as amount_range,
    COUNT(*) as decline_count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ()), 2) as percentage
FROM analytics_events 
WHERE event_type = 'decision_outcome'
    AND decision = 'DECLINE'
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

-- 8. Decline Reasons by Customer Segment (Last 30 Days)
SELECT 
    CASE 
        WHEN tags LIKE '%premium_customer%' THEN 'Premium'
        WHEN tags LIKE '%high_risk%' THEN 'High Risk'
        WHEN tags LIKE '%new_customer%' THEN 'New Customer'
        WHEN tags LIKE '%returning_customer%' THEN 'Returning Customer'
        ELSE 'Standard'
    END as customer_segment,
    COUNT(*) as decline_count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ()), 2) as percentage
FROM analytics_events 
WHERE event_type = 'decision_outcome'
    AND decision = 'DECLINE'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
GROUP BY customer_segment
ORDER BY decline_count DESC;

-- 9. Decline Reasons by Time (Daily - Last 30 Days)
SELECT 
    DATE(FROM_UNIXTIME(timestamp)) as date_bucket,
    COUNT(*) as decline_count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ()), 2) as percentage
FROM analytics_events 
WHERE event_type = 'decision_outcome'
    AND decision = 'DECLINE'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
GROUP BY date_bucket
ORDER BY date_bucket;

-- 10. Decline Reasons by Merchant (Last 30 Days)
SELECT 
    merchant_id,
    COUNT(*) as decline_count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ()), 2) as percentage
FROM analytics_events 
WHERE event_type = 'decision_outcome'
    AND decision = 'DECLINE'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
GROUP BY merchant_id
ORDER BY decline_count DESC;

-- 11. Decline Reasons by Confidence Score (Last 30 Days)
SELECT 
    CASE 
        WHEN confidence_score IS NULL THEN 'Unknown'
        WHEN confidence_score < 0.3 THEN 'Very Low (<30%)'
        WHEN confidence_score < 0.5 THEN 'Low (30-50%)'
        WHEN confidence_score < 0.7 THEN 'Medium (50-70%)'
        WHEN confidence_score < 0.9 THEN 'High (70-90%)'
        ELSE 'Very High (>90%)'
    END as confidence_level,
    COUNT(*) as decline_count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ()), 2) as percentage
FROM analytics_events 
WHERE event_type = 'decision_outcome'
    AND decision = 'DECLINE'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
GROUP BY confidence_level
ORDER BY 
    CASE confidence_level
        WHEN 'Very Low (<30%)' THEN 1
        WHEN 'Low (30-50%)' THEN 2
        WHEN 'Medium (50-70%)' THEN 3
        WHEN 'High (70-90%)' THEN 4
        WHEN 'Very High (>90%)' THEN 5
        ELSE 6
    END;

-- 12. Decline Reasons by Risk Score (Last 30 Days)
SELECT 
    CASE 
        WHEN metadata->>'$.final_score' IS NULL THEN 'Unknown'
        WHEN CAST(metadata->>'$.final_score' AS DECIMAL(5,2)) < 50 THEN 'Low Risk (<50)'
        WHEN CAST(metadata->>'$.final_score' AS DECIMAL(5,2)) < 70 THEN 'Medium Risk (50-70)'
        WHEN CAST(metadata->>'$.final_score' AS DECIMAL(5,2)) < 85 THEN 'High Risk (70-85)'
        WHEN CAST(metadata->>'$.final_score' AS DECIMAL(5,2)) < 95 THEN 'Very High Risk (85-95)'
        ELSE 'Extreme Risk (>95)'
    END as risk_level,
    COUNT(*) as decline_count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ()), 2) as percentage
FROM analytics_events 
WHERE event_type = 'decision_outcome'
    AND decision = 'DECLINE'
    AND timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
GROUP BY risk_level
ORDER BY 
    CASE risk_level
        WHEN 'Low Risk (<50)' THEN 1
        WHEN 'Medium Risk (50-70)' THEN 2
        WHEN 'High Risk (70-85)' THEN 3
        WHEN 'Very High Risk (85-95)' THEN 4
        WHEN 'Extreme Risk (>95)' THEN 5
        ELSE 6
    END;
