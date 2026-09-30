// ============================================================
// PROJECT: Neo4j + Power BI E-commerce
// FILE: 27_device_source_conversion.cypher
//
// BUSINESS QUESTION:
//
// Which Device + Traffic Source combinations perform best?
//
// We calculate:
//
// - Sessions
// - Converted Sessions
// - Conversion Rate
// - Revenue
// - Average Order Value
//
// ============================================================


// ------------------------------------------------------------
// 1. START WITH EVERY SESSION
// ------------------------------------------------------------

MATCH (s:Session)


// ------------------------------------------------------------
// 2. FIND AN ORDER IF THE SESSION CONVERTED
// ------------------------------------------------------------

OPTIONAL MATCH (s)-[:CONVERTED_TO]->(o:Order)


// ------------------------------------------------------------
// 3. GROUP BY DEVICE AND SOURCE
// ------------------------------------------------------------

WITH
    s.device AS device,
    s.source AS source,

    count(DISTINCT s) AS sessions,

    count(DISTINCT o) AS converted_sessions,

    coalesce(
        sum(o.total_usd),
        0.0
    ) AS revenue_usd


// ------------------------------------------------------------
// 4. CALCULATE BUSINESS METRICS
// ------------------------------------------------------------

RETURN

    device,

    source,

    sessions,

    converted_sessions,

    round(
        100.0 * converted_sessions /
        sessions,
        2
    ) AS conversion_rate_pct,

    round(
        revenue_usd,
        2
    ) AS revenue_usd,

    round(
        CASE
            WHEN converted_sessions = 0
            THEN 0
            ELSE revenue_usd / converted_sessions
        END,
        2
    ) AS avg_order_value_usd

ORDER BY
    conversion_rate_pct DESC,
    revenue_usd DESC;