// ============================================================
// PROJECT: Neo4j + Power BI E-commerce
// FILE: 16_funnel_analysis.cypher
//
// BUSINESS QUESTION:
//
// How many customer sessions reached:
//
// 1. Page View
// 2. Add to Cart
// 3. Checkout
// 4. Purchase
//
// IMPORTANT:
//
// We count SESSIONS, not individual Events.
//
// Example:
//
// One Session may contain:
//
// page_view
// page_view
// page_view
// add_to_cart
//
// That is still ONE session at the Page View stage,
// not three.
// ============================================================


// ------------------------------------------------------------
// 1. LOOK AT EVERY SESSION
// ------------------------------------------------------------

MATCH (s:Session)


// Find all Events belonging to this Session
OPTIONAL MATCH (s)-[:HAS_EVENT]->(e:Event)


// Collect the different event types found in the Session
WITH
    s,
    collect(DISTINCT e.event_type) AS event_types


// ------------------------------------------------------------
// 2. COUNT SESSIONS THAT REACHED EACH FUNNEL STAGE
// ------------------------------------------------------------

WITH
    count(s) AS total_sessions,

    sum(
        CASE
            WHEN 'page_view' IN event_types
            THEN 1
            ELSE 0
        END
    ) AS page_view_sessions,

    sum(
        CASE
            WHEN 'add_to_cart' IN event_types
            THEN 1
            ELSE 0
        END
    ) AS add_to_cart_sessions,

    sum(
        CASE
            WHEN 'checkout' IN event_types
            THEN 1
            ELSE 0
        END
    ) AS checkout_sessions,

    sum(
        CASE
            WHEN 'purchase' IN event_types
            THEN 1
            ELSE 0
        END
    ) AS purchase_sessions


// ------------------------------------------------------------
// 3. RETURN POWER BI FRIENDLY OUTPUT
// ------------------------------------------------------------

RETURN
    total_sessions,

    page_view_sessions,
    add_to_cart_sessions,
    checkout_sessions,
    purchase_sessions,

    round(
        100.0 * add_to_cart_sessions /
        page_view_sessions,
        2
    ) AS view_to_cart_pct,

    round(
        100.0 * checkout_sessions /
        add_to_cart_sessions,
        2
    ) AS cart_to_checkout_pct,

    round(
        100.0 * purchase_sessions /
        checkout_sessions,
        2
    ) AS checkout_to_purchase_pct,

    round(
        100.0 * purchase_sessions /
        total_sessions,
        2
    ) AS overall_conversion_pct;