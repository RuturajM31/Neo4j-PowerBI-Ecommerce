// ============================================================
// PROJECT: Neo4j + Power BI E-commerce
// FILE: 12_load_reviews.cypher
//
// WHAT ARE WE DOING?
//
// 1. Create Review nodes
// 2. Connect Order -> Review
// 3. Connect Review -> Product
//
// Final graph:
//
// Order
//   |
// HAS_REVIEW
//   v
// Review
//   |
// ABOUT
//   v
// Product
//
// ============================================================


// Read reviews.csv
LOAD CSV WITH HEADERS
FROM 'file:///bi_ecommerce/reviews.csv' AS row


// ------------------------------------------------------------
// FIND THE ORDER
// ------------------------------------------------------------

// Find the Order connected to this Review
MATCH (o:Order {
    order_id: toInteger(row.order_id)
})


// ------------------------------------------------------------
// FIND THE PRODUCT
// ------------------------------------------------------------

// Find the Product this Review is about
MATCH (p:Product {
    product_id: toInteger(row.product_id)
})


// ------------------------------------------------------------
// CREATE THE REVIEW NODE
// ------------------------------------------------------------

// Create one Review node for each review_id
MERGE (r:Review {
    review_id: toInteger(row.review_id)
})


// Add Review information
SET
    r.rating = toInteger(row.rating),
    r.review_text = row.review_text,
    r.review_time = datetime(row.review_time)


// ------------------------------------------------------------
// CONNECT ORDER -> REVIEW
// ------------------------------------------------------------

// This means:
//
// "This Order has this Review"
MERGE (o)-[:HAS_REVIEW]->(r)


// ------------------------------------------------------------
// CONNECT REVIEW -> PRODUCT
// ------------------------------------------------------------

// This means:
//
// "This Review is about this Product"
MERGE (r)-[:ABOUT]->(p)


// ------------------------------------------------------------
// COUNT WHAT WE CREATED
// ------------------------------------------------------------

WITH count(*) AS rows_processed


// Count Review nodes
MATCH (r:Review)

WITH
    rows_processed,
    count(r) AS review_count


// Count Order -> Review arrows
MATCH (:Order)-[h:HAS_REVIEW]->(:Review)

WITH
    rows_processed,
    review_count,
    count(h) AS has_review_relationships


// Count Review -> Product arrows
MATCH (:Review)-[a:ABOUT]->(:Product)

RETURN
    rows_processed,
    review_count,
    has_review_relationships,
    count(a) AS about_relationships;