// ============================================================
// PROJECT: Neo4j + Power BI E-commerce
// FILE: 25_category_copurchase.cypher
//
// BUSINESS QUESTION:
//
// Which Product categories commonly occur together
// inside the same Order?
//
// This is more stable than individual SKU pairs because
// the dataset contains 1,197 different Products.
// ============================================================


// ------------------------------------------------------------
// 1. FIND TWO PRODUCTS INSIDE THE SAME ORDER
// ------------------------------------------------------------

MATCH (o:Order)-[:CONTAINS]->(p1:Product)
MATCH (o)-[:CONTAINS]->(p2:Product)


// Avoid:
//
// Product A + Product B
// Product B + Product A
//
// being counted twice.
WHERE p1.product_id < p2.product_id


// ------------------------------------------------------------
// 2. TURN PRODUCT PAIRS INTO CATEGORY PAIRS
// ------------------------------------------------------------

// Put category names into a consistent order.
//
// Example:
//
// Beauty + Books
//
// instead of sometimes:
//
// Books + Beauty
WITH
    o,

    CASE
        WHEN p1.category <= p2.category
        THEN p1.category
        ELSE p2.category
    END AS category_1,

    CASE
        WHEN p1.category <= p2.category
        THEN p2.category
        ELSE p1.category
    END AS category_2


// ------------------------------------------------------------
// 3. COUNT EACH ORDER ONLY ONCE PER CATEGORY PAIR
// ------------------------------------------------------------

WITH DISTINCT
    o,
    category_1,
    category_2


// ------------------------------------------------------------
// 4. COUNT ORDERS FOR EACH CATEGORY COMBINATION
// ------------------------------------------------------------

WITH
    category_1,
    category_2,
    count(DISTINCT o) AS orders_together,

    COUNT {
        MATCH (:Order)
    } AS total_orders


// ------------------------------------------------------------
// 5. RETURN POWER BI FRIENDLY OUTPUT
// ------------------------------------------------------------

RETURN

    category_1,

    category_2,

    orders_together,

    round(
        100.0 * orders_together /
        total_orders,
        2
    ) AS percentage_of_all_orders,

    CASE
        WHEN category_1 = category_2
        THEN 'Same Category'
        ELSE 'Cross Category'
    END AS relationship_type

ORDER BY
    orders_together DESC;