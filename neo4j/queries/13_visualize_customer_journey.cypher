// ============================================================
// PROJECT: Neo4j + Power BI E-commerce
// FILE: 13_visualize_customer_journey.cypher
//
// WHAT ARE WE DOING?
//
// Show ONE complete customer journey as a connected graph.
//
// Customer
//    |
//  STARTED
//    v
// Session
//    |
// HAS_EVENT
//    v
// First Event
//    |
//   NEXT
//    v
// Event
//    |
//   NEXT
//    v
// Purchase
//    |
// GENERATED
//    v
// Order
//
// ============================================================


// ------------------------------------------------------------
// FIND A SESSION THAT ENDED IN A PURCHASE
// ------------------------------------------------------------

// Find Customer -> Session
MATCH (c:Customer)-[:STARTED]->(s:Session)

// Find Session -> Order
MATCH (s)-[:CONVERTED_TO]->(o:Order)

// Find the Purchase Event that created that Order
MATCH (s)-[:HAS_EVENT]->(purchase:Event)-[:GENERATED]->(o)

WHERE purchase.event_type = 'purchase'


// ------------------------------------------------------------
// FIND THE FIRST EVENT IN THAT SESSION
// ------------------------------------------------------------

// Find an Event belonging to the Session
MATCH (s)-[:HAS_EVENT]->(first:Event)

// It is the first Event if no other Event in this
// same Session points to it using NEXT.
WHERE NOT EXISTS {

    MATCH (s)-[:HAS_EVENT]->(previous:Event)-[:NEXT]->(first)

}


// ------------------------------------------------------------
// BUILD THE THREE CONNECTED PARTS
// ------------------------------------------------------------

// Customer -> Session -> First Event
MATCH customer_to_start =
    (c)-[:STARTED]->(s)-[:HAS_EVENT]->(first)


// First Event -> ... -> Purchase Event
MATCH event_journey =
    (first)-[:NEXT*0..]->(purchase)


// Purchase Event -> Order
MATCH purchase_to_order =
    (purchase)-[:GENERATED]->(o)


// Only show one complete journey
WITH
    customer_to_start,
    event_journey,
    purchase_to_order

LIMIT 1


// ------------------------------------------------------------
// RETURN THE COMPLETE CONNECTED GRAPH
// ------------------------------------------------------------

RETURN
    customer_to_start,
    event_journey,
    purchase_to_order;