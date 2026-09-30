// ============================================================
// PROJECT: Neo4j + Power BI E-commerce
// FILE: 08_load_orders.cypher
//
// WHAT ARE WE DOING?
//
// 1. Create Order nodes
// 2. Connect each Purchase Event to its real Order
//
// Purchase Event -> GENERATED -> Order
//
// ============================================================


// ============================================================
// PART 1 - CREATE ORDER NODES
// ============================================================

LOAD CSV WITH HEADERS
FROM 'file:///bi_ecommerce/orders.csv' AS row

CALL (row) {

    // Create one Order node for every order_id
    MERGE (o:Order {
        order_id: toInteger(row.order_id)
    })

    // Add useful Order information
    SET
        o.order_time = datetime(row.order_time),
        o.payment_method = row.payment_method,
        o.discount_pct = toFloat(row.discount_pct),
        o.subtotal_usd = toFloat(row.subtotal_usd),
        o.total_usd = toFloat(row.total_usd),
        o.country = row.country,
        o.device = row.device,
        o.source = row.source

} IN TRANSACTIONS OF 10000 ROWS;


// ============================================================
// PART 2 - CONNECT PURCHASE EVENT TO ORDER
// ============================================================

LOAD CSV WITH HEADERS
FROM 'file:///bi_ecommerce/events.csv' AS row

// Only Purchase Events have an order_id
WITH row
WHERE row.order_id IS NOT NULL
  AND row.order_id <> ''

CALL (row) {

    // Find the Purchase Event
    MATCH (e:Event {
        event_id: toInteger(row.event_id)
    })

    // Find the matching Order
    MATCH (o:Order {
        order_id: toInteger(row.order_id)
    })

    // Connect:
    //
    // Purchase Event -> GENERATED -> Order
    MERGE (e)-[:GENERATED]->(o)

} IN TRANSACTIONS OF 10000 ROWS;


// ============================================================
// PART 3 - CHECK THE RESULT
// ============================================================

MATCH (o:Order)

WITH count(o) AS order_count

MATCH (:Event)-[r:GENERATED]->(:Order)

RETURN
    order_count,
    count(r) AS generated_relationships;