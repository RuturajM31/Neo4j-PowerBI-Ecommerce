// ============================================================
// PROJECT: Neo4j + Power BI E-commerce
// FILE: 07_connect_events_products.cypher
//
// WHAT ARE WE DOING?
//
// Connect product-related Events to Products.
//
// Example:
//
// Page View
//     |
// INTERACTED_WITH
//     |
//     v
// Product
//
// Add To Cart
//     |
// INTERACTED_WITH
//     |
//     v
// Product
//
// ============================================================


// ============================================================
// PART 1 - CREATE EVENT -> PRODUCT CONNECTIONS
// ============================================================

LOAD CSV WITH HEADERS
FROM 'file:///bi_ecommerce/events.csv' AS row

// Only use Events that actually contain a product_id
WITH row
WHERE row.product_id IS NOT NULL
  AND row.product_id <> ''

CALL (row) {

    // Find the Event
    MATCH (e:Event {
        event_id: toInteger(row.event_id)
    })

    // Find the Product
    MATCH (p:Product {
        product_id: toInteger(row.product_id)
    })

    // Connect Event -> Product
    MERGE (e)-[:INTERACTED_WITH]->(p)

} IN TRANSACTIONS OF 10000 ROWS;


// ============================================================
// PART 2 - CHECK THE RESULT
// ============================================================

MATCH (:Event)-[r:INTERACTED_WITH]->(:Product)

RETURN
    count(r) AS product_interactions;