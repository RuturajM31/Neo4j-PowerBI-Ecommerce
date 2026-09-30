// ============================================================
// PROJECT: Neo4j + Power BI E-commerce
// FILE: 15_visualize_purchase_journey.cypher
//
// PURPOSE:
//
// Show ONE strong customer purchase journey:
//
// Customer
//    |
//  STARTED
//    v
// Session
//    |
// HAS_EVENT
//    v
// Event -> NEXT -> Event -> ... -> Purchase
//                                  |
//                               GENERATED
//                                  v
//                                Order
//                           /       |       \
//                     CONTAINS   CONTAINS   CONTAINS
//                        v          v          v
//                    Product    Product    Product
//
// We intentionally choose an Order with multiple products
// so the graph is useful for presentation.
// ============================================================


// ============================================================
// 1. FIND A GOOD ORDER FOR VISUALISATION
// ============================================================

// Find orders and count how many different products they contain.
MATCH (o:Order)-[:CONTAINS]->(product:Product)

WITH
    o,
    count(DISTINCT product) AS product_count

// We want an interesting order,
// not a boring order containing only one product.
WHERE product_count >= 3

// Prefer an order containing more products.
ORDER BY product_count DESC

// Choose only ONE order.
LIMIT 1


// ============================================================
// 2. FIND THE CUSTOMER AND SESSION
// ============================================================

MATCH customer_session =
    (c:Customer)-[:STARTED]->(s:Session)

MATCH (s)-[:CONVERTED_TO]->(o)


// ============================================================
// 3. FIND THE PURCHASE EVENT
// ============================================================

MATCH purchase_order =
    (purchase:Event)-[:GENERATED]->(o)

MATCH (s)-[:HAS_EVENT]->(purchase)

WHERE purchase.event_type = 'purchase'


// ============================================================
// 4. FIND THE FIRST EVENT IN THIS SESSION
// ============================================================

MATCH (s)-[:HAS_EVENT]->(first:Event)

WHERE NOT EXISTS {

    MATCH (s)-[:HAS_EVENT]->(previous:Event)-[:NEXT]->(first)

}


// ============================================================
// 5. CONNECT SESSION TO FIRST EVENT
// ============================================================

MATCH session_start =
    (s)-[:HAS_EVENT]->(first)


// ============================================================
// 6. FOLLOW THE COMPLETE EVENT JOURNEY
// ============================================================

MATCH event_journey =
    (first)-[:NEXT*0..]->(purchase)


// ============================================================
// 7. FIND ALL PRODUCTS ACTUALLY PURCHASED
// ============================================================

MATCH order_product =
    (o)-[:CONTAINS]->(p:Product)


// ============================================================
// 8. RETURN EVERYTHING AS REAL GRAPH PATHS
// ============================================================

RETURN
    customer_session,
    session_start,
    event_journey,
    purchase_order,
    order_product;