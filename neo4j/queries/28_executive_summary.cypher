// ============================================================
// PROJECT: Neo4j + Power BI E-commerce
// FILE: 28_executive_summary.cypher
//
// PURPOSE:
//
// Create one final executive KPI summary for Power BI.
//
// Metrics:
//
// - Total Customers
// - Total Sessions
// - Total Orders
// - Total Revenue
// - Average Order Value
// - Overall Conversion Rate
// - Purchasing Customers
// - Repeat Buyers
// - Repeat Buyer Rate
// - Total Reviews
//
// ============================================================


// ------------------------------------------------------------
// 1. TOTAL CUSTOMERS
// ------------------------------------------------------------

CALL () {

    MATCH (c:Customer)

    RETURN
        count(c) AS total_customers
}


// ------------------------------------------------------------
// 2. TOTAL SESSIONS
// ------------------------------------------------------------

CALL () {

    MATCH (s:Session)

    RETURN
        count(s) AS total_sessions
}


// ------------------------------------------------------------
// 3. ORDER + REVENUE METRICS
// ------------------------------------------------------------

CALL () {

    MATCH (o:Order)

    RETURN

        count(o) AS total_orders,

        sum(o.total_usd) AS total_revenue_usd,

        avg(o.total_usd) AS avg_order_value_usd
}


// ------------------------------------------------------------
// 4. CUSTOMER PURCHASE BEHAVIOUR
// ------------------------------------------------------------

CALL () {

    MATCH (c:Customer)-[:PLACED]->(o:Order)

    WITH
        c,
        count(o) AS customer_orders

    RETURN

        count(c) AS purchasing_customers,

        sum(
            CASE
                WHEN customer_orders > 1
                THEN 1
                ELSE 0
            END
        ) AS repeat_buyers
}


// ------------------------------------------------------------
// 5. REVIEWS
// ------------------------------------------------------------

CALL () {

    MATCH (r:Review)

    RETURN
        count(r) AS total_reviews
}


// ------------------------------------------------------------
// 6. FINAL POWER BI FRIENDLY OUTPUT
// ------------------------------------------------------------

RETURN

    total_customers,

    total_sessions,

    total_orders,

    round(
        total_revenue_usd,
        2
    ) AS total_revenue_usd,

    round(
        avg_order_value_usd,
        2
    ) AS avg_order_value_usd,

    round(
        100.0 * total_orders /
        total_sessions,
        2
    ) AS conversion_rate_pct,

    purchasing_customers,

    round(
        100.0 * purchasing_customers /
        total_customers,
        2
    ) AS purchasing_customer_pct,

    repeat_buyers,

    round(
        100.0 * repeat_buyers /
        purchasing_customers,
        2
    ) AS repeat_buyer_pct_of_buyers,

    total_reviews;