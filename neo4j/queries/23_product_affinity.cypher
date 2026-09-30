// ============================================================
// PROJECT: Neo4j + Power BI E-commerce
// FILE: 23_product_affinity.cypher
//
// BUSINESS QUESTION:
//
// Which Products have the strongest purchase affinity?
//
// METRICS:
//
// Co-purchase Orders
// Support
// Confidence Product 1 -> Product 2
// Confidence Product 2 -> Product 1
// Lift
//
// ============================================================


// ------------------------------------------------------------
// 1. FIND PRODUCT PAIRS BOUGHT IN THE SAME ORDER
// ------------------------------------------------------------

MATCH (o:Order)-[:CONTAINS]->(p1:Product)

MATCH (o)-[:CONTAINS]->(p2:Product)


// Keep only one version of each pair:
//
// A + B
//
// not:
//
// A + B
// B + A
WHERE p1.product_id < p2.product_id


// ------------------------------------------------------------
// 2. COUNT ORDERS CONTAINING BOTH PRODUCTS
// ------------------------------------------------------------

WITH
    p1,
    p2,
    count(DISTINCT o) AS copurchase_orders


// ------------------------------------------------------------
// 3. IGNORE EXTREMELY RARE PAIRS
// ------------------------------------------------------------

// We already saw that this dataset has a sparse
// product-level network.
//
// Require at least 3 shared Orders so that we do not
// rank a pair based on only one accidental purchase.
WHERE copurchase_orders >= 3


// ------------------------------------------------------------
// 4. COUNT ORDERS CONTAINING EACH PRODUCT
// ------------------------------------------------------------

WITH
    p1,
    p2,
    copurchase_orders,

    COUNT {
        MATCH (:Order)-[:CONTAINS]->(p1)
    } AS product_1_orders,

    COUNT {
        MATCH (:Order)-[:CONTAINS]->(p2)
    } AS product_2_orders,

    COUNT {
        MATCH (:Order)
    } AS total_orders


// ------------------------------------------------------------
// 5. CALCULATE AFFINITY METRICS
// ------------------------------------------------------------

WITH
    p1,
    p2,
    copurchase_orders,
    product_1_orders,
    product_2_orders,
    total_orders,

    // Percentage of ALL Orders containing both Products
    100.0 * copurchase_orders /
    total_orders AS support_pct,

    // When Product 1 is bought,
    // how often is Product 2 also bought?
    100.0 * copurchase_orders /
    product_1_orders AS confidence_1_to_2_pct,

    // When Product 2 is bought,
    // how often is Product 1 also bought?
    100.0 * copurchase_orders /
    product_2_orders AS confidence_2_to_1_pct,

    // Strength compared with random chance
    (
        1.0 * copurchase_orders * total_orders
    )
    /
    (
        product_1_orders * product_2_orders
    ) AS lift


// ------------------------------------------------------------
// 6. RETURN POWER BI FRIENDLY OUTPUT
// ------------------------------------------------------------

RETURN

    p1.product_id AS product_1_id,

    p1.name AS product_1_name,

    p1.category AS product_1_category,

    p2.product_id AS product_2_id,

    p2.name AS product_2_name,

    p2.category AS product_2_category,

    copurchase_orders,

    product_1_orders,

    product_2_orders,

    round(
        support_pct,
        3
    ) AS support_pct,

    round(
        confidence_1_to_2_pct,
        2
    ) AS confidence_1_to_2_pct,

    round(
        confidence_2_to_1_pct,
        2
    ) AS confidence_2_to_1_pct,

    round(
        lift,
        2
    ) AS lift

ORDER BY
    lift DESC,
    copurchase_orders DESC

LIMIT 20;