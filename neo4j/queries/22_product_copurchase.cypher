// ============================================================
// PROJECT: Neo4j + Power BI E-commerce
// FILE: 22_product_copurchase.cypher
//
// BUSINESS QUESTION:
//
// Which Products are most commonly purchased together
// inside the same Order?
//
// Example:
//
// Order
//  ├── Product A
//  ├── Product B
//  └── Product C
//
// Creates analytical pairs:
//
// A + B
// A + C
// B + C
//
// ============================================================


// ------------------------------------------------------------
// 1. FIND TWO PRODUCTS INSIDE THE SAME ORDER
// ------------------------------------------------------------

MATCH (o:Order)-[:CONTAINS]->(p1:Product)

MATCH (o)-[:CONTAINS]->(p2:Product)


// ------------------------------------------------------------
// 2. REMOVE DUPLICATE / REVERSED PAIRS
// ------------------------------------------------------------

// Without this:
//
// Laptop + Mouse
//
// and
//
// Mouse + Laptop
//
// would both be counted.
//
// We keep only one direction.
WHERE p1.product_id < p2.product_id


// ------------------------------------------------------------
// 3. COUNT ORDERS CONTAINING EACH PAIR
// ------------------------------------------------------------

WITH
    p1,
    p2,
    count(DISTINCT o) AS copurchase_orders


// ------------------------------------------------------------
// 4. RETURN POWER BI FRIENDLY OUTPUT
// ------------------------------------------------------------

RETURN

    p1.product_id AS product_1_id,

    p1.name AS product_1_name,

    p1.category AS product_1_category,

    p2.product_id AS product_2_id,

    p2.name AS product_2_name,

    p2.category AS product_2_category,

    copurchase_orders

ORDER BY
    copurchase_orders DESC

LIMIT 20;