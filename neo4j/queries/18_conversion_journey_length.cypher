// ============================================================
// PROJECT: Neo4j + Power BI E-commerce
// FILE: 18_conversion_journey_length.cypher
//
// BUSINESS QUESTION:
//
// How many Events / NEXT steps does a successful
// customer journey contain before purchase?
//
// Example:
//
// page_view
//    ↓ NEXT
// add_to_cart
//    ↓ NEXT
// checkout
//    ↓ NEXT
// purchase
//
// Events     = 4
// NEXT steps = 3
//
// ============================================================


// ------------------------------------------------------------
// 1. FIND EVERY CONVERTED SESSION
// ------------------------------------------------------------

MATCH (s:Session)-[:CONVERTED_TO]->(o:Order)


// Find the Purchase Event that created the Order
MATCH (s)-[:HAS_EVENT]->(purchase:Event)-[:GENERATED]->(o)

WHERE purchase.event_type = 'purchase'


// ------------------------------------------------------------
// 2. FIND THE FIRST EVENT OF EACH SESSION
// ------------------------------------------------------------

MATCH (s)-[:HAS_EVENT]->(first:Event)

WHERE NOT EXISTS {

    MATCH (s)-[:HAS_EVENT]->(:Event)-[:NEXT]->(first)

}


// ------------------------------------------------------------
// 3. FOLLOW THE REAL NEXT PATH TO PURCHASE
// ------------------------------------------------------------

MATCH journey =
    (first)-[:NEXT*0..]->(purchase)


// ------------------------------------------------------------
// 4. CALCULATE JOURNEY LENGTH
// ------------------------------------------------------------

WITH
    s,

    // Number of arrows between Events
    length(journey) AS next_steps,

    // Number of Event nodes in the journey
    length(journey) + 1 AS event_count


// ------------------------------------------------------------
// 5. RETURN SUMMARY METRICS
// ------------------------------------------------------------

RETURN

    count(s) AS converted_sessions,

    round(avg(event_count), 2)
        AS avg_events_to_purchase,

    percentileCont(event_count, 0.5)
        AS median_events_to_purchase,

    min(event_count)
        AS min_events_to_purchase,

    max(event_count)
        AS max_events_to_purchase,

    round(avg(next_steps), 2)
        AS avg_next_steps_to_purchase;