// ============================================================
// PROJECT: Neo4j + Power BI E-commerce
// FILE: 24_cross_sell_opportunities.cypher
//
// BUSINESS QUESTION:
//
// When customers purchased Product A,
// what other Product B did they VIEW
// during the same Session but NOT purchase?
//
// Example:
//
// Customer views:
// Laptop + Mouse
//
// Customer buys:
// Laptop
//
// Possible cross-sell:
// Laptop -> Mouse
//
// ============================================================


// ------------------------------------------------------------
// 1. FIND SUCCESSFUL SESSIONS
// ------------------------------------------------------------

MATCH (s:Session)-[:CONVERTED_TO]->(o:Order)


// ------------------------------------------------------------
// 2. FIND PRODUCTS ACTUALLY PURCHASED
// ------------------------------------------------------------

MATCH (o)-[:CONTAINS]->(bought:Product)


// ------------------------------------------------------------
// 3. FIND PRODUCTS VIEWED IN THE SAME SESSION
// ------------------------------------------------------------

MATCH (s)-[:HAS_EVENT]->(e:Event)
      -[:INTERACTED_WITH]->(viewed:Product)


// ------------------------------------------------------------
// 4. KEEP ONLY PAGE VIEWS
//
// ALSO:
//
// - Do not recommend the Product already purchased
// - Do not recommend another Product that was also
//   already included in the same Order
// ------------------------------------------------------------

WHERE
    e.event_type = 'page_view'

    AND bought.product_id <> viewed.product_id

    AND NOT EXISTS {

        MATCH (o)-[:CONTAINS]->(viewed)

    }


// ------------------------------------------------------------
// 5. COUNT EACH SESSION ONLY ONCE PER PRODUCT PAIR
// ------------------------------------------------------------

// A customer might view the same Product several times.
//
// Example:
//
// Mouse
// Mouse
// Mouse
//
// We still count this as ONE opportunity
// for that Session.
WITH DISTINCT
    s,
    bought,
    viewed


// ------------------------------------------------------------
// 6. COUNT CROSS-SELL OPPORTUNITIES
// ------------------------------------------------------------

WITH
    bought,
    viewed,
    count(s) AS opportunity_sessions


// ------------------------------------------------------------
// 7. RETURN POWER BI FRIENDLY OUTPUT
// ------------------------------------------------------------

RETURN

    bought.product_id
        AS purchased_product_id,

    bought.name
        AS purchased_product_name,

    bought.category
        AS purchased_product_category,

    viewed.product_id
        AS cross_sell_product_id,

    viewed.name
        AS cross_sell_product_name,

    viewed.category
        AS cross_sell_product_category,

    opportunity_sessions

ORDER BY
    opportunity_sessions DESC

LIMIT 20;