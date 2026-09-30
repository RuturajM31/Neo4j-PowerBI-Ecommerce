// ============================================================
// PROJECT: Neo4j + Power BI E-commerce
// FILE: 06_create_next_relationships.cypher
//
// WHAT ARE WE DOING?
//
// We are connecting each Event to the Event that happened next.
//
// Example:
//
// Page View
//    |
//   NEXT
//    v
// Add To Cart
//    |
//   NEXT
//    v
// Checkout
//    |
//   NEXT
//    v
// Purchase
//
// ============================================================


// ============================================================
// PART 1 - CREATE EVENT -> NEXT -> EVENT
// ============================================================

// Read the cleaned events.csv file
LOAD CSV WITH HEADERS
FROM 'file:///bi_ecommerce/events.csv' AS row

// Only use rows that actually have a next event.
// The final Event in each Session has no next_event_id.
WITH row
WHERE row.next_event_id IS NOT NULL
  AND row.next_event_id <> ''

CALL (row) {

    // Find the current Event
    MATCH (current:Event {
        event_id: toInteger(row.event_id)
    })

    // Find the next Event
    MATCH (next:Event {
        event_id: toInteger(row.next_event_id)
    })

    // Create the journey arrow
    MERGE (current)-[:NEXT]->(next)

} IN TRANSACTIONS OF 10000 ROWS;


// ============================================================
// PART 2 - CHECK THE RESULT
// ============================================================

// Count all NEXT relationships
MATCH (:Event)-[r:NEXT]->(:Event)

RETURN
    count(r) AS next_relationships;