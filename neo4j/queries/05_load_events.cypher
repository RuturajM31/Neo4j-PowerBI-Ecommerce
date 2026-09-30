// ============================================================
// PROJECT: Neo4j + Power BI E-commerce
// FILE: 05_load_events.cypher
//
// WHAT THIS QUERY DOES:
//
// 1. Reads events.csv
// 2. Creates one Event node for every website action
// 3. Connects every Event to the correct Session
//
// Final graph piece:
//
// Session -> HAS_EVENT -> Event
//
// ============================================================


// ============================================================
// PART 1 - CREATE EVENTS + CONNECT THEM TO SESSIONS
// ============================================================

LOAD CSV WITH HEADERS
FROM 'file:///bi_ecommerce/events.csv' AS row

CALL (row) {

    // Find the session this event belongs to
    MATCH (s:Session {
        session_id: toInteger(row.session_id)
    })

    // Create the Event node
    MERGE (e:Event {
        event_id: toInteger(row.event_id)
    })

    // Save useful event information
    SET
        e.timestamp = datetime(row.timestamp),
        e.event_type = row.event_type,
        e.product_id = CASE
            WHEN row.product_id = '' THEN null
            ELSE toInteger(toFloat(row.product_id))
        END,
        e.qty = CASE
            WHEN row.qty = '' THEN null
            ELSE toInteger(toFloat(row.qty))
        END,
        e.cart_size = CASE
            WHEN row.cart_size = '' THEN null
            ELSE toInteger(toFloat(row.cart_size))
        END,
        e.payment = CASE
            WHEN row.payment = '' THEN null
            ELSE row.payment
        END,
        e.discount_pct = CASE
            WHEN row.discount_pct = '' THEN null
            ELSE toFloat(row.discount_pct)
        END,
        e.amount_usd = CASE
            WHEN row.amount_usd = '' THEN null
            ELSE toFloat(row.amount_usd)
        END

    // Connect Session -> Event
    MERGE (s)-[:HAS_EVENT]->(e)

} IN TRANSACTIONS OF 10000 ROWS;


// ============================================================
// PART 2 - CHECK THE RESULT
// ============================================================

MATCH (e:Event)
WITH count(e) AS event_count

MATCH (:Session)-[r:HAS_EVENT]->(:Event)

RETURN
    event_count,
    count(r) AS has_event_relationships;