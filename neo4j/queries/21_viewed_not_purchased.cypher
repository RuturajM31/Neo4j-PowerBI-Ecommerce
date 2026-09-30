// ============================================================
// PROJECT: Neo4j + Power BI E-commerce
// FILE: 21_viewed_not_purchased.cypher
//
// BUSINESS QUESTION:
//
// Which Products are viewed often
// but are not purchased in the same Session?
//
// Example:
//
// Product A
//
// Viewed in:        1,000 Sessions
// Purchased in:       250 Sessions
//
// Viewed Not Bought:  750 Sessions
//
// ============================================================


// ------------------------------------------------------------
// 1. FIND PRODUCT VIEWS
// ------------------------------------------------------------

// Find:
//
// Session -> Event -> Product
//
// where the Event is specifically a page_view.
MATCH (s:Session)-[:HAS_EVENT]->(e:Event)
      -[:INTERACTED_WITH]->(p:Product)

WHERE e.event_type = 'page_view'


// ------------------------------------------------------------
// 2. KEEP ONLY ONE SESSION-PRODUCT COMBINATION
// ------------------------------------------------------------

// A customer may view the same Product several times
// during one Session.
//
// Example:
//
// Laptop
// Laptop
// Laptop
//
// We still count that as ONE viewing Session.
WITH DISTINCT
    s,
    p


// ------------------------------------------------------------
// 3. CHECK WHETHER THAT PRODUCT WAS BOUGHT
// ------------------------------------------------------------

WITH
    s,
    p,

    EXISTS {

        MATCH (s)-[:CONVERTED_TO]->(o:Order)
              -[:CONTAINS]->(p)

    } AS product_was_purchased


// ------------------------------------------------------------
// 4. AGGREGATE BY PRODUCT
// ------------------------------------------------------------

WITH
    p,

    count(*) AS viewed_sessions,

    sum(
        CASE
            WHEN product_was_purchased
            THEN 1
            ELSE 0
        END
    ) AS purchased_after_view_sessions


// ------------------------------------------------------------
// 5. CALCULATE MISSED PURCHASE OPPORTUNITY
// ------------------------------------------------------------

WITH
    p,
    viewed_sessions,
    purchased_after_view_sessions,

    viewed_sessions -
    purchased_after_view_sessions
        AS viewed_not_purchased_sessions


// ------------------------------------------------------------
// 6. RETURN POWER BI FRIENDLY OUTPUT
// ------------------------------------------------------------

RETURN

    p.product_id AS product_id,

    p.name AS product_name,

    p.category AS category,

    viewed_sessions,

    purchased_after_view_sessions,

    viewed_not_purchased_sessions,

    round(
        100.0 *
        purchased_after_view_sessions /
        viewed_sessions,
        2
    ) AS view_to_purchase_pct,

    round(
        100.0 *
        viewed_not_purchased_sessions /
        viewed_sessions,
        2
    ) AS view_without_purchase_pct

ORDER BY
    viewed_not_purchased_sessions DESC

LIMIT 20;