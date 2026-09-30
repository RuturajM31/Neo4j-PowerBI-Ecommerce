// ============================================================
// PROJECT: Neo4j + Power BI E-commerce
// FILE: 09_connect_orders.cypher
//
// WHAT ARE WE DOING?
//
// Connect Orders to:
// 1. The Customer who placed them
// 2. The Session that produced them
//
// Customer -> PLACED -> Order
// Session -> CONVERTED_TO -> Order
// ============================================================


// ============================================================
// CREATE BOTH CONNECTIONS
// ============================================================

LOAD CSV WITH HEADERS
FROM 'file:///bi_ecommerce/orders.csv' AS row

CALL (row) {

    // Find the Customer
    MATCH (c:Customer {
        customer_id: toInteger(row.customer_id)
    })

    // Find the Session
    MATCH (s:Session {
        session_id: toInteger(row.session_id)
    })

    // Find the Order
    MATCH (o:Order {
        order_id: toInteger(row.order_id)
    })

    // Customer placed the Order
    MERGE (c)-[:PLACED]->(o)

    // Session converted into the Order
    MERGE (s)-[:CONVERTED_TO]->(o)

} IN TRANSACTIONS OF 10000 ROWS;


// ============================================================
// CHECK THE RESULT
// ============================================================

MATCH (:Customer)-[p:PLACED]->(:Order)
WITH count(p) AS placed_relationships

MATCH (:Session)-[c:CONVERTED_TO]->(:Order)

RETURN
    placed_relationships,
    count(c) AS converted_relationships;