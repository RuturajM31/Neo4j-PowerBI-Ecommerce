// ============================================================
// PROJECT: Neo4j + Power BI E-commerce
// FILE: 17_abandonment_analysis.cypher
//
// BUSINESS QUESTION:
//
// Where do customer sessions abandon the funnel?
//
// We place every Session into ONE final outcome:
//
// 1. Browse Only
// 2. Cart Abandonment
// 3. Checkout Abandonment
// 4. Purchased
//
// This makes the categories mutually exclusive.
// Every Session appears exactly once.
// ============================================================


// ------------------------------------------------------------
// 1. LOOK AT EVERY SESSION
// ------------------------------------------------------------

MATCH (s:Session)

OPTIONAL MATCH (s)-[:HAS_EVENT]->(e:Event)


// Collect all event types found inside each Session
WITH
    s,
    collect(DISTINCT e.event_type) AS event_types


// ------------------------------------------------------------
// 2. CLASSIFY THE SESSION
// ------------------------------------------------------------

WITH
    s,

    CASE

        // Session completed a purchase
        WHEN 'purchase' IN event_types
        THEN 'Purchased'

        // Session reached checkout but did not purchase
        WHEN 'checkout' IN event_types
        THEN 'Checkout Abandonment'

        // Session added something to cart
        // but never reached checkout
        WHEN 'add_to_cart' IN event_types
        THEN 'Cart Abandonment'

        // Session only browsed products/pages
        ELSE 'Browse Only'

    END AS journey_outcome


// ------------------------------------------------------------
// 3. STORE ALL SESSION OUTCOMES
// ------------------------------------------------------------

WITH
    collect(journey_outcome) AS outcomes,
    count(s) AS total_sessions


// Turn the collected results back into rows
UNWIND outcomes AS journey_outcome


// ------------------------------------------------------------
// 4. COUNT EACH OUTCOME
// ------------------------------------------------------------

WITH
    journey_outcome,
    count(*) AS sessions,
    total_sessions


// ------------------------------------------------------------
// 5. ADD DISPLAY ORDER
// ------------------------------------------------------------

WITH
    journey_outcome,
    sessions,
    total_sessions,

    CASE journey_outcome
        WHEN 'Browse Only' THEN 1
        WHEN 'Cart Abandonment' THEN 2
        WHEN 'Checkout Abandonment' THEN 3
        WHEN 'Purchased' THEN 4
    END AS stage_order


// ------------------------------------------------------------
// 6. RETURN POWER BI FRIENDLY OUTPUT
// ------------------------------------------------------------

RETURN
    stage_order,
    journey_outcome,
    sessions,

    round(
        100.0 * sessions / total_sessions,
        2
    ) AS percentage_of_sessions

ORDER BY stage_order;