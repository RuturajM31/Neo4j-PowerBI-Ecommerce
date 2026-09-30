// ============================================================
// PROJECT: Neo4j + Power BI E-commerce
// FILE: 19_conversion_time.cypher
//
// BUSINESS QUESTION:
//
// How long does a converted Session take
// from Session start to Purchase?
//
// Example:
//
// Session start:  09:00
// Purchase:       09:07
//
// Conversion time = 7 minutes
// ============================================================


// ------------------------------------------------------------
// 1. FIND EVERY SESSION THAT PURCHASED
// ------------------------------------------------------------

MATCH (s:Session)-[:CONVERTED_TO]->(o:Order)


// Find the Purchase Event that generated the Order
MATCH (s)-[:HAS_EVENT]->(purchase:Event)-[:GENERATED]->(o)

WHERE purchase.event_type = 'purchase'


// ------------------------------------------------------------
// 2. CALCULATE TIME TO PURCHASE
// ------------------------------------------------------------

WITH
    s,
    o,
    purchase,

    duration.inSeconds(
        s.start_time,
        purchase.timestamp
    ).seconds / 60.0 AS conversion_minutes


// ------------------------------------------------------------
// 3. RETURN SUMMARY METRICS
// ------------------------------------------------------------

RETURN

    count(*) AS converted_sessions,

    round(
        avg(conversion_minutes),
        2
    ) AS avg_conversion_minutes,

    round(
        percentileCont(conversion_minutes, 0.5),
        2
    ) AS median_conversion_minutes,

    round(
        min(conversion_minutes),
        2
    ) AS fastest_conversion_minutes,

    round(
        max(conversion_minutes),
        2
    ) AS slowest_conversion_minutes;