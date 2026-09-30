// ============================================================
// PROJECT: Neo4j + Power BI E-commerce
// FILE: 26_customer_value_segments.cypher
//
// BUSINESS QUESTION:
//
// How valuable are our Customers?
//
// We divide Customers into:
//
// 1. No Purchase
// 2. One-Time Buyer
// 3. Repeat Buyer
//
// Then calculate:
//
// - Customers
// - Orders
// - Revenue
// - Average Orders per Customer
// - Average Revenue per Customer
//
// ============================================================


// ------------------------------------------------------------
// 1. START WITH EVERY CUSTOMER
// ------------------------------------------------------------

MATCH (c:Customer)


// ------------------------------------------------------------
// 2. FIND THEIR ORDERS
// ------------------------------------------------------------

OPTIONAL MATCH (c)-[:PLACED]->(o:Order)


// ------------------------------------------------------------
// 3. CALCULATE CUSTOMER-LEVEL METRICS
// ------------------------------------------------------------

WITH
    c,

    count(o) AS order_count,

    coalesce(
        sum(o.total_usd),
        0.0
    ) AS customer_revenue


// ------------------------------------------------------------
// 4. CLASSIFY EACH CUSTOMER
// ------------------------------------------------------------

WITH
    c,
    order_count,
    customer_revenue,

    CASE

        WHEN order_count = 0
        THEN 'No Purchase'

        WHEN order_count = 1
        THEN 'One-Time Buyer'

        ELSE 'Repeat Buyer'

    END AS customer_segment,

    CASE

        WHEN order_count = 0
        THEN 1

        WHEN order_count = 1
        THEN 2

        ELSE 3

    END AS segment_order


// ------------------------------------------------------------
// 5. AGGREGATE BY CUSTOMER SEGMENT
// ------------------------------------------------------------

WITH
    segment_order,
    customer_segment,

    count(c) AS customers,

    sum(order_count) AS orders,

    sum(customer_revenue) AS revenue,

    avg(order_count) AS avg_orders_per_customer,

    avg(customer_revenue) AS avg_revenue_per_customer


// ------------------------------------------------------------
// 6. RETURN POWER BI FRIENDLY OUTPUT
// ------------------------------------------------------------

RETURN

    segment_order,

    customer_segment,

    customers,

    orders,

    round(
        revenue,
        2
    ) AS revenue_usd,

    round(
        avg_orders_per_customer,
        2
    ) AS avg_orders_per_customer,

    round(
        avg_revenue_per_customer,
        2
    ) AS avg_revenue_per_customer_usd

ORDER BY segment_order;